import os
import threading
import types
from typing import Optional, Tuple

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from multiprocessing import Process, Pipe, ProcessError
import traceback


class MigrationError(BaseException):
    # Exception wrapper to create exception with traceback from child process
    pass


class MigrationProcess(Process):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent_conn, self._child_conn = Pipe()
        self._exception: Optional[Tuple[Exception, str]] = None

    def run(self):
        try:
            super().run()
            self._child_conn.send(None)
        except Exception as e:
            tb = traceback.format_exc()
            self._child_conn.send((e, tb))

    @property
    def exception(self) -> Optional[Tuple[Exception, str]]:
        if self._parent_conn.poll():
            self._exception = self._parent_conn.recv()
        return self._exception


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


active_databases = {}


def execute_migration(engine: Engine, alembic_path: Optional[str] = None):
    def isolated_migration_process():
        nonlocal engine, alembic_path
        from openmodule.database.migration import migrate_database
        migrate_database(engine, alembic_path)

    p = MigrationProcess(target=isolated_migration_process)
    try:
        p.start()
        p.join(timeout=5 * 60)  # default 5 min timeout -> exception/sentry in service
    except ProcessError:
        raise
    finally:
        if p.is_alive():
            p.kill()  # send SIGKILL
            p.join()  # wait for death
            p.close()  # release all resources associated with the process

    if p.exitcode is None:
        raise TimeoutError("The duration of the migration exceeded the timeout")

    if p.exception is not None:
        # piped exception with full traceback from child process -> if migration failed e.g. bad migration file
        e, tb = p.exception
        raise MigrationError(tb) from e


def database_path(db_folder, db_name):
    return os.path.join(db_folder, db_name) + ".sqlite3"


def get_database(db_folder: str, name: str, alembic_path: Optional[str] = None):
    global active_databases
    tmp = database_path(db_folder, name)
    assert active_databases.get(tmp) is None, f"database {tmp} already exists," \
                                              f" check if it was shutdown before a new one was created"
    os.makedirs(db_folder, exist_ok=True)
    path = f"sqlite:///{tmp}"
    engine = create_engine(path, poolclass=StaticPool, connect_args={'check_same_thread': False})

    # migration executed in a separate process -> no alembic import in main process
    execute_migration(engine, alembic_path)

    active_databases[tmp] = engine

    return engine


class DatabaseContext:
    def __init__(self, database: 'Database', expire_on_commit=True):
        self.database = database
        self.expire_on_commit = expire_on_commit

    def __enter__(self) -> Session:
        return self.database.__enter__(expire_on_commit=self.expire_on_commit)

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.database.__exit__(exc_type, exc_val, exc_tb)


class SessionWrapper(Session):
    _closed = False

    def __getattribute__(self, item):
        attr = super().__getattribute__(item)
        if isinstance(attr, types.MethodType) and self._closed:
            raise AssertionError("Session is already closed")
        return attr

    def close(self):
        super().close()
        self._closed = True


class Database:
    active_session: Optional[Session]

    def __init__(self, database_folder, name="database", alembic_path=None):
        self.db_folder = database_folder
        self.name = name
        self._engine = get_database(database_folder, name, alembic_path)
        self._session = sessionmaker(bind=self._engine, class_=SessionWrapper)
        self.active_session = None
        self.lock = threading.RLock()

    def is_open(self):
        return bool(self._session)

    def shutdown(self):
        assert self.is_open(), "database is already closed, you called shutdown twice somewhere"

        with self.lock:
            self._session = None
            global active_databases
            active_databases.pop(database_path(self.db_folder, self.name), None)

    def __call__(self, expire_on_commit=True) -> DatabaseContext:
        return DatabaseContext(self, expire_on_commit=expire_on_commit)

    def __enter__(self, expire_on_commit=True) -> Session:
        assert self._session, "Session is already closed"
        self.lock.acquire()
        self.active_session = self._session(expire_on_commit=expire_on_commit)
        return self.active_session

    def flush(self, objects=None):
        assert self._session and self.active_session, "Session is already closed"
        self.active_session.flush(objects)

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                self.active_session.commit()
            else:
                self.active_session.rollback()
        finally:
            self.active_session.close()
            self.active_session = None
            self.lock.release()

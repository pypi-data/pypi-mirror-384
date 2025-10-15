import os
import time
from threading import Thread
from unittest import TestCase
from unittest.mock import patch

import freezegun
import sqlalchemy
from alembic import command
from alembic.runtime.migration import MigrationContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound, DetachedInstanceError

from openmodule.config import settings
from openmodule.database.database import Database, active_databases, database_path, MigrationError
from openmodule.database.migration import alembic_config
from openmodule.utils.db_helper import update_query, delete_query
from openmodule_test.database import SQLiteTestMixin
from tests.database_models_migration import DatabaseCascadeDeleteParentModel, DatabaseCascadeDeleteChildModel
from tests.database_models_test import DatabaseTestModel


class DatabaseTest(SQLiteTestMixin, TestCase):
    alembic_path = "../tests/test_database"

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            os.unlink(database_path(cls.get_database_folder(), "asdf"))
        except FileNotFoundError:
            pass

    def test_filter(self):
        data = [DatabaseTestModel(value1=x, value2=x % 3) for x in range(5)]
        with self.database as db:
            db.add_all(data)
            self.assertEqual(1, db.query(DatabaseTestModel).filter_by(value1=0).count())
            self.assertEqual(2, db.query(DatabaseTestModel).filter_by(value2=0).count())

        with self.database as db:
            query = db.query(DatabaseTestModel).filter_by(value2=0)
            res = query.filter_by(value1=0)
            self.assertEqual(1, len(list(res)))
            self.assertEqual(0, res[0].value1)
            self.assertEqual(0, res[0].value2)

    def test_update_filter(self):
        data = [DatabaseTestModel(value1=x, value2=x % 3) for x in range(5)]
        with self.database as db:
            db.add_all(data)

            rows_changed = update_query(db, db.query(DatabaseTestModel).filter_by(value2=2), dict(value1=7))
            self.assertEqual(rows_changed, 1)
            results = db.query(DatabaseTestModel).filter_by(value2=2)
            self.assertEqual(2, results[0].value2)

            rows_changed = update_query(db, db.query(DatabaseTestModel).filter_by(value2=1), dict(value1=7))
            self.assertEqual(rows_changed, 2)
            results = db.query(DatabaseTestModel).filter_by(value2=1)
            self.assertEqual(2, results.count())
            self.assertEqual(3, db.query(DatabaseTestModel).filter_by(value1=7).count())

    def test_expire_on_commit(self):
        with self.database as db:
            model = DatabaseTestModel(value1=1)
            db.add(model)
            db.flush()
            pk = model.id

        # default expire is True
        with self.database as db:
            model = db.get(DatabaseTestModel, pk)
        with self.assertRaises(DetachedInstanceError):
            self.assertEqual(model.value1, 1)

        # default expire also is True when calling database
        with self.database() as db:
            model = db.get(DatabaseTestModel, pk)
        with self.assertRaises(DetachedInstanceError):
            self.assertEqual(model.value1, 1)

        # passing expire_on_commit disables the expire
        with self.database(expire_on_commit=False) as db:
            model = db.get(DatabaseTestModel, pk)
        self.assertEqual(model.value1, 1)

    def test_delete_2(self):
        """
        test that added models are indeed added, even when calling expire_all
        (could not find a proper proof in the documentation)
        """

        # step 1 fill some test data
        data = [DatabaseTestModel(value1=x, value2=x) for x in range(10)]
        with self.database as db:
            db.add_all(data)

        # step 2 add data in the same session where we call expire_all
        my_new_data = DatabaseTestModel(value1=100, value2=100)
        with self.database as db:
            db.add(my_new_data)

            # delete query calls db.expire_all()
            # lets call it one more time here just for good meausure
            delete_query(db, db.query(DatabaseTestModel).filter(DatabaseTestModel.value1 <= 10))
            db.expire_all()

        # we now check that the newly added data is still here
        with self.database as db:
            self.assertEqual(1, db.query(DatabaseTestModel).filter_by(value1=100).count())
            self.assertEqual(0, db.query(DatabaseTestModel).filter(DatabaseTestModel.value1 <= 10).count())

    def test_delete(self):
        data = [DatabaseTestModel(value1=x % 5, value2=x % 3) for x in range(10)]
        with self.database as db:
            db.add_all(data)

            delete_query(db, db.query(DatabaseTestModel).filter_by(value2=0, value1=17))
            self.assertEqual(10, len(db.query(DatabaseTestModel).all()))

            nr_deleted = delete_query(db, db.query(DatabaseTestModel).filter_by(value2=0))
            self.assertEqual(6, len(db.query(DatabaseTestModel).all()))
            self.assertEqual(4, nr_deleted)

            nr_deleted = delete_query(db, db.query(DatabaseTestModel).filter_by(value2=1, value1=1))
            self.assertEqual(5, len(db.query(DatabaseTestModel).all()))
            self.assertEqual(1, nr_deleted)

            tmp = db.query(DatabaseTestModel).filter_by(value1=4)

            self.assertTrue(1, tmp.count())
            db.delete(tmp[0])
            self.assertFalse(any(x.value1 == 4 for x in db.query(DatabaseTestModel).all()))

    def test_rollback(self):
        a = DatabaseTestModel(value1=5, value2=0)
        with self.database as db:
            db.add(a)
            db.flush()
            tmp = a.id
        with self.assertRaises(Exception):
            with self.database as db:
                a.value1 = 6
                db.add(a)
                raise Exception("asdf")

        with self.database as db:
            current = db.get(DatabaseTestModel, tmp)
            self.assertEqual(5, current.value1)
            self.assertEqual(1, len(db.query(DatabaseTestModel).all()))

    def test_exception_on_commit(self):
        with self.database as db:
            db.add(DatabaseTestModel(id="id1", value1=1))

        with self.assertRaises(IntegrityError) as e:
            with self.database as db:  # this add will fail, because id1 is already in use
                db.add(DatabaseTestModel(id="id1", value1=1))
        self.assertIn("UNIQUE constraint", str(e.exception))

        # test that we are able to use the database afterwards
        with self.database as db:
            db.add(DatabaseTestModel(id="id2", value1=2))

    def test_database_transaction_is_single_threaded(self):
        """
        this test starts a second thread, which waits for 0.5s, after that it tries to acquire the database
        and read the value of an object. The main thread in the meantime blocks for 2 seconds, and after that
        writes something to the database. Both threads check that the other is at the expected state.
        The test shows that the transaction is single threaded, and all threads are blocked while
        a thread has acquired the db
        """
        main_thread_position = ""
        second_thread_position = ""
        second_thread_value = None

        # initial setup model(1) with value = initial
        with self.database as db:
            model = DatabaseTestModel(id="1", string="initial")
            db.add(model)

        def second_thread():
            nonlocal second_thread_position, second_thread_value
            time.sleep(0.5)
            second_thread_position = "acquiring"
            with self.database as db:
                self.assertEqual(main_thread_position, "end")
                second_thread_model: DatabaseTestModel = db.get(DatabaseTestModel, "1")
                second_thread_value = second_thread_model.string

        thread = Thread(target=second_thread)
        thread.start()

        with self.database as db:
            time.sleep(2)
            self.assertEqual(second_thread_position, "acquiring")
            model = db.get(DatabaseTestModel, "1")
            model.string = "changed"
            db.add(model)
            main_thread_position = "end"

        thread.join()
        self.assertEqual(second_thread_value, "changed")

    def test_multiple_databases(self):
        db1 = Database(self.get_database_folder(), name="asdf", alembic_path=self.alembic_path)
        with db1 as db:
            db.add(DatabaseTestModel(value1=0, value2=4))
        with self.assertRaises(Exception) as e:
            Database(self.get_database_folder(), name="asdf", alembic_path=self.alembic_path)
        self.assertIn("already exists", str(e.exception))
        self.assertTrue(os.path.exists(os.path.join(self.get_database_folder(), "asdf.sqlite3")))

    def test_get(self):
        with self.database as db:
            base = db.query(DatabaseTestModel)
            res = db.get(DatabaseTestModel, "asdf")
            self.assertIsNone(res)

            with self.assertRaises(Exception) as e:
                base.one()
            self.assertEqual(NoResultFound, type(e.exception))

            res = base.one_or_none()
            self.assertIsNone(res)

            res = base.first()
            self.assertIsNone(res)

            model1 = DatabaseTestModel()
            model2 = DatabaseTestModel()
            db.add(model1)
            db.add(model2)

            res = base.first()
            self.assertIsNotNone(res)

            with self.assertRaises(Exception) as e:
                base.one_or_none()
            self.assertEqual(MultipleResultsFound, type(e.exception))

    def test_closed_session(self):
        model = DatabaseTestModel()

        with self.database as db:
            db.add(model)

        with self.assertRaises(AssertionError) as e:
            db.query(DatabaseTestModel).all()
        self.assertIn("Session is already closed", str(e.exception))

    def test_closed_session_write(self):
        model = DatabaseTestModel()
        model1 = DatabaseTestModel()

        with self.database as db:
            db.add(model)

        with self.assertRaises(AssertionError) as e:
            db.add(model1)
        self.assertIn("Session is already closed", str(e.exception))


class ShutdownTestCase(TestCase):
    alembic_path = "../tests/test_database"

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            os.unlink(database_path(settings.DATABASE_FOLDER, "shutdown"))
        except FileNotFoundError:
            pass

    def get_database(self):
        return Database(settings.DATABASE_FOLDER, name="shutdown", alembic_path=self.alembic_path)

    def check_db_present(self, value):
        tmp = database_path(settings.DATABASE_FOLDER, "shutdown")
        if value:
            self.assertIn(tmp, active_databases.keys())
        else:
            self.assertNotIn(tmp, active_databases.keys())

    def test_shutdown(self):
        self.check_db_present(False)
        database = self.get_database()
        self.check_db_present(True)
        database.shutdown()
        self.check_db_present(False)

    def test_shutdown_while_using(self):
        database = self.get_database()

        def hold_db():
            with database as db:
                time.sleep(3)

        thread = Thread(target=hold_db)
        thread.start()
        self.assertEqual(True, thread.is_alive())
        self.check_db_present(True)
        database.shutdown()
        self.assertEqual(False, thread.is_alive())
        self.check_db_present(False)

    def test_double_shutdown(self):
        database = self.get_database()
        self.check_db_present(True)

        database.shutdown()

        with self.assertRaises(AssertionError) as e:
            database.shutdown()
        self.assertIn("already closed", str(e.exception))
        self.check_db_present(False)


class MultipleMigrationTest(SQLiteTestMixin, TestCase):
    """
    there was an issue, which prevented a database from beeing migrated multiple times in a single process
    """
    create_database = False
    alembic_path = "../tests/test_database"

    def test_migrate_1(self):
        database = Database(self.get_database_folder(), self.database_name, self.alembic_path)
        with database as db:
            self.assertEqual(0, db.query(DatabaseTestModel).count())
        database.shutdown()
        self.delete_database(database)

    def test_migrate_2(self):
        database = Database(self.get_database_folder(), self.database_name, self.alembic_path)
        with database as db:
            self.assertEqual(0, db.query(DatabaseTestModel).count())
        database.shutdown()
        self.delete_database(database)


class CascadeDeleteTest(SQLiteTestMixin, TestCase):
    alembic_path = "../tests/migration_test_database"

    def test_cascade_delete(self):
        with self.database as db:
            self.assertEqual(1, db.query(DatabaseCascadeDeleteParentModel).count(),
                             "parent model deleted during migration")
            self.assertEqual(1, db.query(DatabaseCascadeDeleteChildModel).count(),
                             "child model deleted during migration")

        with self.database as db:
            parent_instance = DatabaseCascadeDeleteParentModel(name=777)
            child_instance = DatabaseCascadeDeleteChildModel(parent=parent_instance)
            db.add(parent_instance)
            db.add(child_instance)

        with self.database as db:
            delete_query(db, db.query(DatabaseCascadeDeleteParentModel)
                         .filter(DatabaseCascadeDeleteParentModel.name == 777))

        with self.database as db:
            self.assertEqual(1, db.query(DatabaseCascadeDeleteParentModel).count(),
                             "parent model was not deleted by above query")
            self.assertEqual(1, db.query(DatabaseCascadeDeleteChildModel).count(),
                             "foreign key constraints seem to be disabled")


class BackupDatabasePreMigrationUpgradeTest(SQLiteTestMixin, TestCase):
    # we use this database because it has three versions
    alembic_path = "../tests/test_access_service_database"
    database_name = "om_test_migration_1"

    def setUp(self):
        super().setUp()
        # we are going to remove all backup databases before the tests
        for filename in os.listdir(self.get_database_folder()):
            if filename.endswith(".backup"):
                os.remove(os.path.join(self.get_database_folder(), filename))

    @freezegun.freeze_time("2024-01-01 00:00:00")
    def test_no_backup_is_created_if_database_does_not_exist(self):
        original_db = f"{self.get_database_folder()}/om_test_migration_1.sqlite3"
        backup_db = f"{self.get_database_folder()}/om_test_migration_1_20240101000000_c821971f9230.sqlite3.backup"
        self.assertTrue(os.path.exists(original_db))
        self.assertFalse(os.path.exists(backup_db))

    @freezegun.freeze_time("2024-01-01 00:00:01")
    def test_backup_is_created_if_database_exists(self):
        original_db = f"{self.get_database_folder()}/om_test_migration_1.sqlite3"
        second_backup_db = f"{self.get_database_folder()}/om_test_migration_1_20240101000001_9ca98a2e5674.sqlite3.backup"
        backup_db = f"{self.get_database_folder()}/om_test_migration_1_20240101000001_c821971f9230.sqlite3.backup"
        self.assertTrue(os.path.exists(original_db))
        self.assertFalse(os.path.exists(backup_db))

        # we have to manually downgrade and upgrade to trigger the backup
        config = alembic_config(self.database._engine, self.alembic_path)
        command.downgrade(config, "c821971f9230")
        self.assertTrue(os.path.exists(original_db))
        self.assertFalse(os.path.exists(backup_db))

        # now we upgrade and a backup database with the revision c821971f9230 should exist, but not the second one
        # wit the revision 9ca98a2e5674
        command.upgrade(config, "7bd4fcd38fde")

        self.assertTrue(os.path.exists(original_db))
        self.assertTrue(os.path.exists(backup_db))
        self.assertFalse(os.path.exists(second_backup_db))
        # revision should now be head revision 7bd4fcd38fde
        with self.database as db:
            original_migration_context = MigrationContext.configure(db.connection())
            self.assertEqual("7bd4fcd38fde", original_migration_context.get_current_revision())
        # backup should still have the downgrade revision c821971f9230
        engine = sqlalchemy.create_engine(f"sqlite:///{backup_db}")
        with engine.connect() as connection:
            backup_migration_context = MigrationContext.configure(connection)
            self.assertEqual("c821971f9230", backup_migration_context.get_current_revision())


class DowngradeMigrationSequenceNameTest(SQLiteTestMixin, TestCase):
    alembic_path = "../tests/migration_test_database"

    def test_downgrade(self):
        # the `sequence_name` parameter was removed from the `pre_downgrade` and `post_downgrade` and the
        # generated alembic migration file should be able to be executed without errors
        config = alembic_config(self.database._engine, self.alembic_path)
        command.downgrade(config, "base")


class DatabaseMigrationProcessFailTest(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            os.unlink(database_path(cls.get_database_folder(), "database"))
        except FileNotFoundError:
            pass

    @classmethod
    def get_database_folder(cls):
        return settings.DATABASE_FOLDER

    def test_bad_migration_table_error(self):
        alembic_path = "../tests/migration_no_such_table_error"
        with self.assertRaises(MigrationError) as cm:
            _ = Database(self.get_database_folder(), alembic_path=alembic_path)
        self.assertIn("sqlalchemy.exc.NoSuchTableError: test_access_model_FAIL", str(cm.exception))

    def test_bad_migration_double_delete_column(self):
        alembic_path = "../tests/migration_double_column_delete_error"
        with self.assertRaises(MigrationError) as cm:
            _ = Database(self.get_database_folder(), alembic_path=alembic_path)
        self.assertIn("KeyError: 'regex'", str(cm.exception))

    def test_fail_process_timeout(self):
        alembic_path = "../tests/migration_test_database"
        from multiprocessing import TimeoutError
        with patch("openmodule.database.database.MigrationProcess.join", side_effect=TimeoutError), \
                self.assertRaises(TimeoutError):
            _ = Database(self.get_database_folder(), alembic_path=alembic_path)

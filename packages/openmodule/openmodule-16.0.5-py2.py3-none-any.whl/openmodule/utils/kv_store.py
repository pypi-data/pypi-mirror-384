import hashlib
import logging
import random
import threading
import time
import uuid
import warnings

import orjson
from sqlalchemy import String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from openmodule import sentry
from openmodule.config import settings, testing
from openmodule.connection_status import ConnectionStatus
from openmodule.core import core
from openmodule.database.database import Database
from openmodule.models.kv_store import ServerSyncResponse, KVSetRequest, KVSyncRequest, KVSyncResponse, KVSetResponse, \
    KVSetRequestKV
from openmodule.models.rpc import ServerRPCRequest
from openmodule.rpc import RPCServer, RPCClient
from openmodule.threading import get_thread_wrapper
from openmodule.utils.db_helper import delete_query


class Base(DeclarativeBase):
    pass


class KVEntry:
    """
    Inherit from this class and add columns that should be parsed from the value coming from the server
        and implement the parse_value method.
    """

    key: Mapped[str] = mapped_column(String, nullable=False, index=True, unique=True)
    e_tag: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True, index=True)

    @classmethod
    def parse_value(cls, _: dict) -> dict | list[Base]:  # pragma: no cover
        """
        This method parses the synced in a list of database entries.
        You can use this method to generate additional local database models.
        """
        raise NotImplementedError

    def comparison_value(self) -> str:  # pragma: no cover
        """
        Only used for KVStoreWithChangedNotification
        return some hash or string. Changed messages are only sent if this value changed for a key
        """
        raise NotImplementedError


class KVStore:
    """
    Inherit this class to create a Key-Value store in the database.
    This class handles syncing with the server.

    database_table: Must be an inherited class of KVEntry.
    suffix: Determines the sync channel for the service.
    """
    database_table: type[KVEntry]
    suffix: str | None = None

    class ETagMismatchException(Exception):
        pass

    def __init__(self, db: Database = None, rpc_client: RPCClient = None, sync_timeout: float = 30.0):
        assert self.database_table != KVEntry, "You must set the database_table attribute to a subclass of KVEntry"
        if self.suffix is None:
            self.service_name = settings.NAME
            self.log = logging.getLogger(self.__class__.__name__)
        else:
            self.service_name = f"{settings.NAME}_{self.suffix}"
            self.log = logging.getLogger(self.__class__.__name__ + f".{self.service_name}")
        self.db = db or core().database
        self.rpc_client = rpc_client or core().rpc_client
        self.sync_timeout = sync_timeout
        self.sync_rpc_entry = None

    def sync_with_server(self) -> RPCClient.RPCEntry:
        """
        This method should be called on startup and on reconnect (use ConnectionStatusListener) to sync the
        Key Value store with the server.
        """
        self.log.debug("Sending sync request")
        timeout = self.sync_timeout - 5
        return self.rpc_client.rpc_non_blocking("rpc-websocket", "server_rpc",
                                                ServerRPCRequest(rpc="kvs_sync", data={"resource": settings.RESOURCE,
                                                                                       "service": self.service_name,
                                                                                       "timeout": timeout}),
                                                timeout=self.sync_timeout)

    def sync_rpc_filter(self, request: KVSetRequest | KVSyncRequest, **__) -> bool:
        """RPCs for kv_sync are filtered by service name"""
        return request.service == self.service_name

    @sentry.trace
    def _kvs_check_etag_mismatched(self, request: KVSetRequest, current_kvs: dict[str, int]):
        for kv in request.kvs:
            current_e_tag = current_kvs.get(kv.key)
            if current_e_tag is None and kv.previous_e_tag is not None:
                self.log.warning(f"Key does not exists but previous ETag given for key {kv.key}")
                raise self.ETagMismatchException("Previous ETag given but not in database")
            elif current_e_tag is not None and kv.previous_e_tag is None:
                self.log.warning(f"Key exists but no previous ETag given for key {kv.key}")
                raise self.ETagMismatchException("No previous ETag")
            elif current_e_tag != kv.previous_e_tag:
                self.log.warning(f"Previous ETag does not match for key {kv.key}")
                raise self.ETagMismatchException("Previous ETag does not match")

    @sentry.trace
    def _kvs_set_parse_kvs(self, kvs: list[KVSetRequestKV]) -> list[KVEntry]:
        to_set = []
        deprecation_warning = False
        for kv in kvs:
            value = orjson.loads(kv.value)
            if value is not None:
                instances = self.database_table.parse_value(value)
                # fallback for old parse_value() implementations
                if isinstance(instances, dict):
                    if not deprecation_warning:
                        warnings.warn("\n\nReturning a dict from parse_value() is deprecated, "
                                      "return a list of database_table instances instead", DeprecationWarning)
                        deprecation_warning = True
                    instances = [self.database_table(key=kv.key, e_tag=kv.e_tag, **instances)]
                # new implementation with database_table instances
                else:
                    assert len(instances) > 0, "parse_value() must return at least one instance"
                    # key and etag values should only be managed by KVStore, therefore we update it here
                    kv_entry_available = False
                    for instance in instances:
                        if isinstance(instance, KVEntry):
                            kv_entry_available = True
                            instance.key = kv.key
                            instance.e_tag = kv.e_tag
                    assert kv_entry_available, "parse_value() must return at least one instance of the database_table"
                to_set += instances
        return to_set

    @sentry.trace
    def kvs_set(self, request: KVSetRequest, _) -> KVSetResponse:
        """
        This method is called by the server to set values in the database.
        It must never be called from the device.
        Database entries must only be created/edited/deleted by this method.
        Entries are never changed, only deleted and recreated with new values and e_tag.
        The e_tag of the current value of a key needs to match previous_e_tag in the request, otherwise the key is
            rejected.
        """
        if not request.kvs:
            return KVSetResponse()
        with self.db() as session:
            current_kvs: dict[str, int] = \
                {kv[0]: kv[1]
                 for kv in session.query(self.database_table).
                 filter(self.database_table.key.in_([kv.key for kv in request.kvs])).
                 with_entities(self.database_table.key, self.database_table.e_tag).all()}
            self._kvs_check_etag_mismatched(request, current_kvs)  # raises Exception on mismatch
            to_set = self._kvs_set_parse_kvs(request.kvs)
            try:
                if current_kvs:
                    delete_query(session, session.query(self.database_table).filter(
                        self.database_table.key.in_(list(current_kvs.keys()))))
                if to_set:
                    session.add_all(to_set)
                session.commit()
            except Exception as e:
                session.rollback()
                raise e
        return KVSetResponse()

    def kvs_sync(self, request: KVSyncRequest, _) -> KVSyncResponse:
        """
        missing_kvs: All keys that were in the request but are not in the database (key=key, e_tag=request.e_tag)
        changed_kvs: All keys that were in the request and are in the database but have a different e_tag
                     (key=key, e_tag=database.e_tag)
        additional_kvs: All keys that were not in the request but are in the database (key=key, e_tag=database.e_tag)
        """
        self.log.debug("Syncing kvs for %s", request.service)
        with self.db() as session:
            current_kvs: dict[str, int] = \
                {kv[0]: kv[1]
                 for kv in session.query(self.database_table).
                 with_entities(self.database_table.key, self.database_table.e_tag).all()}
        changed_kvs = {}
        missing_kvs = {}
        for key, server_e_tag in request.kvs.items():
            device_e_tag = current_kvs.pop(key, None)
            if device_e_tag is None:
                missing_kvs[key] = server_e_tag
            elif device_e_tag != server_e_tag:
                changed_kvs[key] = device_e_tag
        additional_kvs = current_kvs
        return KVSyncResponse(additions=additional_kvs, changes=changed_kvs, missing=missing_kvs)

    def _log_sync_rpc_response(self, rpc_entry: RPCClient.RPCEntry, conn_id: str) -> bool:
        """
        Waits for the RPC to finish and logs the response
        :return: if successful
        """
        self.log.debug("Parsing sync response")
        try:
            rpc_entry.result(ServerSyncResponse)
            return True
        except RPCClient.TimeoutError:
            if core().connection_listener.changed(conn_id):
                self.log.warning("Connection loss during sync")
            else:
                self.log.error("Timeout syncing kvs")
        except RPCClient.CancelError:
            if core().connection_listener.changed(conn_id):
                self.log.warning("Connection loss during sync")
            else:
                self.log.error("Cancelled waiting for result of syncing kvs")
        except RPCClient.ValidationError:
            self.log.exception("Error parsing sync response")
        except RPCClient.RPCServerError as e:
            if len(e.args) > 0 and e.args[0] == "request_timeout" and core().connection_listener.changed(conn_id):
                self.log.warning("Connection loss during sync")
            else:
                self.log.exception("Error on server side in sync")
        except (RPCClient.ServerHandlerError, RPCClient.ServerValidationError, RPCClient.ServerFilterError):
            self.log.exception("Error on server side in sync")
        except Exception:
            self.log.exception("Unexpected exception in sync response")
        return False

    @sentry.trace
    def sync(self, conn_id: str) -> bool:
        self.sync_rpc_entry = self.sync_with_server()
        success = self._log_sync_rpc_response(self.sync_rpc_entry, conn_id)
        self.sync_rpc_entry = None
        if success:  # if sync was successful cancel retries
            return True
        return False


class KVStoreHandler:
    def __init__(self, db: Database = None, rpc_client: RPCClient = None, *stores_cls: type[KVStore],
                 sync_timeout: float = 30.0):
        self.db = db or core().database
        self.rpc_client = rpc_client or core().rpc_client
        self.sync_timeout = sync_timeout
        self.log = logging.getLogger(self.__class__.__name__)
        self.running = True
        self.event = threading.Event()
        self.run_thread: threading.Thread | None = None
        self.stores: list[KVStore] = []
        for cls in stores_cls:
            self.add_kvstore(cls)

    def add_kvstore(self, store_cls: type[KVStore]):
        assert self.run_thread is None, "You must add all stores before calling `run_as_thread()`"
        assert store_cls.suffix not in [store.suffix for store in self.stores], f"Suffix '{store_cls.suffix}' " \
                                                                                f"already used by another store"
        store = store_cls(db=self.db, rpc_client=self.rpc_client, sync_timeout=self.sync_timeout)
        self.stores.append(store)

    def register_rpcs(self, rpc_server: RPCServer) -> None:
        """
        Must be called on startup to register the RPCs
        The MultipleKVStores will filter the RPCs by service name
        """
        rpc_server.register_handler("kv_sync", "set", KVSetRequest, KVSetResponse, self._kvs_set)
        rpc_server.register_handler("kv_sync", "sync", KVSyncRequest, KVSyncResponse, self._kvs_sync)
        rpc_server.add_filter(self._rpc_filter, channel="kv_sync")

    def _rpc_filter(self, request: KVSetRequest | KVSyncRequest, _message: None, _handler: None) -> bool:
        """RPCs are filtered by service name"""
        return any(store.sync_rpc_filter(request) for store in self.stores)

    @sentry.trace
    def _kvs_set(self, request: KVSetRequest, _) -> KVSetResponse | None:
        """Calls the correct kv set function for the correct store"""
        for store in self.stores:
            if store.sync_rpc_filter(request):
                return store.kvs_set(request, _)
        return None

    @sentry.trace
    def _kvs_sync(self, request: KVSyncRequest, _) -> KVSyncResponse | None:
        """Calls the correct kv sync function for the correct store"""
        for store in self.stores:
            if store.sync_rpc_filter(request):
                return store.kvs_sync(request, _)
        return None

    @staticmethod
    def _random_offset_for_sync_with_server() -> float:
        if testing():  # we disable this functionality for testing, because we don't want to wait 10s (worst case)
            return 0.0
        service_name_hash = hashlib.sha256(settings.NAME.encode("utf-8")).hexdigest()
        rnd = random.Random(int(service_name_hash, 16))
        return rnd.uniform(0.0, 10.0)

    def _wait_for_change_to_online(self):
        while self.running:
            changed = core().connection_listener.changed(id(self))  # always true first time after startup
            if changed and core().connection_listener.get() in (ConnectionStatus.startup, ConnectionStatus.online) and \
                    core().connection_listener.previous in (ConnectionStatus.shutdown, ConnectionStatus.offline):
                return True
            self.event.wait(1)
        return False

    def run(self):
        """We only sync on startup and on reconnect"""
        conn_id = uuid.uuid4().hex
        try:
            while self.running:
                if self._wait_for_change_to_online():
                    # on start or reconnect up we add a random offset to the sync,
                    # so that not all KV store instances sync at the same time
                    self.event.wait(self._random_offset_for_sync_with_server())
                    # sync all stores
                    for store in self.stores:
                        while self.running:
                            start = time.time()
                            if core().connection_listener.get() not in (ConnectionStatus.startup,
                                                                        ConnectionStatus.online):
                                # cancel trying to sync if offline
                                break
                            core().connection_listener.changed(conn_id)
                            if store.sync(conn_id):
                                # if sync was successful cancel retries
                                break
                            # we try again as long we are still alive
                            if self.running:
                                self.event.wait(max(0.0, self.sync_timeout - (time.time() - start)))
        except KeyboardInterrupt:
            self.log.warning("KeyboardInterrupt received, shutting down...")
        except Exception:
            self.log.exception("Unexpected exception in KVStore Handler run")

    def run_as_thread(self):
        self.run_thread = threading.Thread(target=get_thread_wrapper(self.run))
        self.run_thread.start()

    def shutdown(self, timeout=5):
        self.running = False
        self.event.set()
        # cancel all outstanding sync RPCs
        for store in self.stores:
            if store.sync_rpc_entry:
                store.sync_rpc_entry.cancel()
        if self.run_thread:
            self.run_thread.join(timeout=timeout)


class KVStoreWithChangedNotification(KVStore):
    def _get_comparison_values(self, kv_entries: list[KVEntry]) -> dict[str, str]:
        """
        make sure your db model has a meaningful `comparison_value` method
        """
        return {kv.key: kv.comparison_value() for kv in kv_entries}

    def _find_changed_kvs(self, new_values: dict[str, str], old_values: dict[str, str]) -> list[str]:
        changed = []
        for key, new_value in new_values.items():
            old_value = old_values.pop(key, None)
            if old_value is None or old_value != new_value:
                changed.append(key)
        changed += list(old_values.keys())
        return changed

    def _send_changed_notification(self, new_values: dict[str, str], old_values: dict[str, str]):  # pragma: no cover
        """
        consider using self._find_changed_kvs when implementing this
        also make sure your db model has a meaningful `comparison_value` method
        """
        raise NotImplementedError

    @sentry.trace
    def kvs_set(self, request: KVSetRequest, _) -> KVSetResponse:
        """
        This method is called by the server to set values in the database.
        It must never be called from the device.
        Database entries must only be created/edited/deleted by this method.
        Entries are never changed, only deleted and recreated with new values and e_tag.
        The e_tag of the current value of a key needs to match previous_e_tag in the request, otherwise the key is
            rejected.
        """
        if not request.kvs:
            return KVSetResponse()
        with self.db() as session:
            full_current_kvs: list[KVEntry] = session.query(self.database_table). \
                filter(self.database_table.key.in_([kv.key for kv in request.kvs]))
            comparison_values = self._get_comparison_values(full_current_kvs)
            current_kvs = {kv.key: kv.e_tag for kv in full_current_kvs}
            self._kvs_check_etag_mismatched(request, current_kvs)  # raises Exception on mismatch
            to_set = self._kvs_set_parse_kvs(request.kvs)
            try:
                if current_kvs:
                    delete_query(session, session.query(self.database_table).filter(
                        self.database_table.key.in_(list(current_kvs.keys()))))
                if to_set:
                    session.add_all(to_set)
                session.commit()
                self._send_changed_notification(self._get_comparison_values(to_set), comparison_values)
            except Exception as e:
                session.rollback()
                raise e
        return KVSetResponse()

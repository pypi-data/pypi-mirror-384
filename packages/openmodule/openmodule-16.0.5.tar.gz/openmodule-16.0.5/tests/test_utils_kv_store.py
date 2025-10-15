import threading
import time
import uuid
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Mapped, DeclarativeBase

from openmodule.config import settings
from openmodule.connection_status import ConnectionStatus, ConnectionStatusMessage
from openmodule.core import core
from openmodule.models.kv_store import KVSetRequest, KVSetRequestKV, KVSyncRequest, KVSetResponse, KVSyncResponse, \
    ServerSyncResponse
from openmodule.models.rpc import ServerRPCRequest
from openmodule.rpc import RPCServer, RPCClient
from openmodule.utils.kv_store import KVStore, KVEntry, KVStoreWithChangedNotification, KVStoreHandler
from openmodule_test.core import OpenModuleCoreTestMixin
from openmodule_test.database import SQLiteTestMixin
from openmodule_test.rpc import RPCServerTestMixin, MockRPCClient


class Base(DeclarativeBase):
    pass


class ExampleKVEntry(KVEntry, Base):
    __tablename__ = "example_kv_entry"

    value_1: Mapped[Optional[str]]
    value_2: Mapped[str]

    @classmethod
    def parse_value(cls, value: dict) -> list['ExampleKVEntry']:
        return [ExampleKVEntry(value_1=value.get("value_1"), value_2=value.get("value_2"))]

    def comparison_value(self) -> str:
        return self.value_1 + "|" + self.value_2

    def __eq__(self, other):
        return isinstance(other, ExampleKVEntry) and self.key == other.key and self.value_1 == other.value_1 \
            and self.value_2 == other.value_2 and self.e_tag == other.e_tag

    def __repr__(self):
        return f"ExampleKVEntry(key={self.key}, value_1={self.value_1}, value_2={self.value_2}, e_tag={self.e_tag})"


class ExampleKVStore(KVStore):
    database_table = ExampleKVEntry


class DatabaseTest(SQLiteTestMixin):
    alembic_path = "../tests/test_kv_store_database"
    database_name = "kvstore"

    def setUp(self) -> None:
        super().setUp()
        self.kv_store = ExampleKVStore(self.database, lambda: None)

    def test_kvs_set(self):
        request = KVSetRequest(service=settings.NAME, kvs=[
            KVSetRequestKV(key="test", value='{"value_1": "test", "value_2": "test2"}', e_tag=1)])
        self.kv_store.kvs_set(request, None)
        with self.database() as session:
            kvs = session.query(ExampleKVEntry).all()
            self.assertEqual(len(kvs), 1)
            self.assertEqual(kvs[0], ExampleKVEntry(key="test", e_tag=1, value_1="test", value_2="test2"))

    def test_kvs_set_override(self):
        with self.database() as session:
            session.add(ExampleKVEntry(key="test", value_1="test", value_2="test2", e_tag=1))
            session.commit()
        request = KVSetRequest(kvs=[
            KVSetRequestKV(key="test", value='{"value_1": "123", "value_2": "234"}', e_tag=2, previous_e_tag=1)
        ], service=settings.NAME)
        self.kv_store.kvs_set(request, None)
        with self.database() as session:
            db_kvs = session.query(ExampleKVEntry).all()
            self.assertEqual(len(db_kvs), 1)
            self.assertEqual(db_kvs[0], ExampleKVEntry(key="test", value_1="123", value_2="234", e_tag=2))

    def test_kvs_set_override_mismatch(self):
        with self.database() as session:
            session.add(ExampleKVEntry(key="test", value_1="test", value_2="test2", e_tag=1))
            session.commit()
        request = KVSetRequest(kvs=[
            KVSetRequestKV(key="test", value='{"value_1": "123", "value_2": "234"}', e_tag=2, previous_e_tag=3)
        ], service=settings.NAME)
        with self.assertRaises(KVStore.ETagMismatchException):
            self.kv_store.kvs_set(request, None)
        with self.database() as session:
            db_kvs = session.query(ExampleKVEntry).all()
            self.assertEqual(len(db_kvs), 1)
            self.assertEqual(db_kvs[0], ExampleKVEntry(key="test", value_1="test", value_2="test2", e_tag=1))

    def test_kvs_set_multiple(self):
        with self.database() as session:
            session.add(ExampleKVEntry(key="test", value_1="test", value_2="test2", e_tag=1))
            session.add(ExampleKVEntry(key="test1", value_1="abc", value_2="def", e_tag=2))
            session.commit()
        request = KVSetRequest(kvs=[
            KVSetRequestKV(key="test", value='{"value_1": "test2", "value_2": "123"}', e_tag=4, previous_e_tag=1),  # ok
            KVSetRequestKV(key="test_new", value='{"value_2": "123", "value_1": "456"}', e_tag=5),  # ok
            KVSetRequestKV(key="test1", value='{"value_1": "ghi", "value_2": "jkl"}', e_tag=6, previous_e_tag=2),  # ok
        ], service=settings.NAME)
        self.kv_store.kvs_set(request, None)
        with self.database() as session:
            db_kvs = session.query(ExampleKVEntry).all()
            self.assertEqual(len(db_kvs), 3)
            self.assertIn(ExampleKVEntry(key="test", value_1="test2", value_2="123", e_tag=4), db_kvs)
            self.assertIn(ExampleKVEntry(key="test_new", value_1="456", value_2="123", e_tag=5), db_kvs)
            self.assertIn(ExampleKVEntry(key="test1", value_1="ghi", value_2="jkl", e_tag=6), db_kvs)

    def test_sync(self):
        with self.database() as session:
            session.add(ExampleKVEntry(key="test", value_1="test", value_2="test2", e_tag=1))  # no change
            session.add(ExampleKVEntry(key="test1", value_1="abc", value_2="def", e_tag=2))  # changed e_tag 5
            session.add(ExampleKVEntry(key="test2", value_1="222", value_2="333", e_tag=3))  # no change
            session.add(ExampleKVEntry(key="test3", value_1="123", value_2="456", e_tag=4))  # addition
            session.commit()

        request = KVSyncRequest(service=settings.NAME, kvs={
            "test": 1,  # no change
            "test1": 5,  # changed e_tag 2
            "test2": 3,  # no change
            "test4": 6  # missing
        })
        response = self.kv_store.kvs_sync(request, None)
        self.assertDictEqual(response.additions, {"test3": 4})
        self.assertDictEqual(response.changes, {"test1": 2})
        self.assertDictEqual(response.missing, {"test4": 6})

    def test_delete_kv(self):
        with self.database() as session:
            session.add(ExampleKVEntry(key="test", value_1="test", value_2="test2", e_tag=1))  # deleting
            session.add(ExampleKVEntry(key="test1", value_1="abc", value_2="def", e_tag=2))  # no change
            session.add(ExampleKVEntry(key="test2", value_1="222", value_2="333", e_tag=3))  # no change
            session.commit()
        request = KVSetRequest(service=settings.NAME, kvs=[
            KVSetRequestKV(key="test", value='null', e_tag=4, previous_e_tag=1)])
        self.kv_store.kvs_set(request, None)
        with self.database() as session:
            db_kvs = session.query(ExampleKVEntry).all()
            self.assertEqual(len(db_kvs), 2)
            self.assertIn(ExampleKVEntry(key="test1", value_1="abc", value_2="def", e_tag=2), db_kvs)
            self.assertIn(ExampleKVEntry(key="test2", value_1="222", value_2="333", e_tag=3), db_kvs)

    def test_wrong_data(self):
        request = KVSetRequest(service=settings.NAME, kvs=[])
        self.kv_store.kvs_set(request, None)
        request = KVSetRequest(service=settings.NAME, kvs=[
            KVSetRequestKV(key="test", value='{"value_2": "123"}', e_tag=4),  # ok
            KVSetRequestKV(key="test1", value='["wrong"]', e_tag=6),  # not a dict
        ])
        with self.assertRaises(AttributeError):
            self.kv_store.kvs_set(request, None)

        request = KVSetRequest(service=settings.NAME, kvs=[
            KVSetRequestKV(key="test", value='{"value_2": "123"}', e_tag=4),  # ok
            KVSetRequestKV(key="test1", value='{"value_2": {"1": 2}}', e_tag=6),  # wrong type
        ])
        with self.assertRaises(SQLAlchemyError):
            self.kv_store.kvs_set(request, None)

        request = KVSetRequest(service=settings.NAME, kvs=[
            KVSetRequestKV(key="test2", value='{"value_2": "123"}', e_tag=4),  # ok
            KVSetRequestKV(key="test3", value='{"value_1": "123"}', e_tag=6),  # value_2 cannot be null
        ])
        with self.assertRaises(SQLAlchemyError):
            self.kv_store.kvs_set(request, None)

    def test_e_tag_mismatch(self):
        with self.database() as session:
            session.add(ExampleKVEntry(key="test", value_1="test", value_2="test2", e_tag=1))  # matches
            session.add(ExampleKVEntry(key="test1", value_1="abc", value_2="def", e_tag=2))  # wrong e_tag
            session.add(ExampleKVEntry(key="test2", value_1="222", value_2="333", e_tag=3))  # no previous e_tag
            session.commit()

        request = KVSetRequest(service=settings.NAME, kvs=[
            KVSetRequestKV(key="test", value='{"value_2": "123"}', e_tag=4, previous_e_tag=1),  # ok
            KVSetRequestKV(key="test1", value='{"value_2": "123"}', e_tag=5, previous_e_tag=6)  # wrong previous e_tag
        ])
        with self.assertRaises(self.kv_store.ETagMismatchException) as e:
            self.kv_store.kvs_set(request, None)
        self.assertEqual(e.exception.args[0], "Previous ETag does not match")

        request = KVSetRequest(service=settings.NAME, kvs=[
            KVSetRequestKV(key="test", value='{"value_2": "123"}', e_tag=4, previous_e_tag=1),  # ok
            KVSetRequestKV(key="test2", value='{"value_2": "123"}', e_tag=5, previous_e_tag=None)  # no previous e_tag
        ])
        with self.assertRaises(self.kv_store.ETagMismatchException) as e:
            self.kv_store.kvs_set(request, None)
        self.assertEqual(e.exception.args[0], "No previous ETag")

        request = KVSetRequest(service=settings.NAME, kvs=[
            KVSetRequestKV(key="test", value='{"value_2": "123"}', e_tag=4, previous_e_tag=1),  # ok
            KVSetRequestKV(key="test3", value='{"value_2": "123"}', e_tag=5, previous_e_tag=6)  # no database e_tag
        ])
        with self.assertRaises(self.kv_store.ETagMismatchException) as e:
            self.kv_store.kvs_set(request, None)
        self.assertEqual(e.exception.args[0], "Previous ETag given but not in database")


class ExampleNotifyKVStore(KVStoreWithChangedNotification):
    database_table = ExampleKVEntry
    changed = []

    def _send_changed_notification(self, new_values: dict[str, str], old_values: dict[str, str]):
        self.changed = self._find_changed_kvs(new_values, old_values)


class DatabaseNotifyTest(DatabaseTest):
    """Inherits from DatabaseTest to ensure the normal KVStore methods function as expected"""
    alembic_path = "../tests/test_kv_store_database"
    database_name = "kvstore"

    def setUp(self) -> None:
        super().setUp()
        self.kv_store = ExampleNotifyKVStore(self.database, lambda: None)

    def test_find_changed_kvs(self):
        new_kvs = [
            ExampleKVEntry(key="1", value_1="test", value_2="test2", e_tag=1),
            ExampleKVEntry(key="2", value_1="test", value_2="test2", e_tag=2),
            ExampleKVEntry(key="3", value_1="test", value_2="test2", e_tag=3)]
        # 0: deleted, 1: changed, 2: changed to same, 3: added
        changed = self.kv_store._find_changed_kvs(
            new_values={"0": "null", "1": "test|test2", "2": "test|test2", "3": "test|test2"},
            old_values={"0": "c|test2", "1": "c|test2", "2": "test|test2"})
        self.assertCountEqual(["0", "1", "3"], changed)

    def test_set_with_changed(self):
        with self.database() as session:
            session.add(ExampleKVEntry(key="1", value_1="test", value_2="test2", e_tag=1))
            session.add(ExampleKVEntry(key="2", value_1="test", value_2="test2", e_tag=2))
            session.add(ExampleKVEntry(key="3", value_1="test", value_2="test2", e_tag=3))
            session.add(ExampleKVEntry(key="4", value_1="test", value_2="test2", e_tag=4))
            session.commit()
        self.kv_store.kvs_set(
            KVSetRequest(
                service="test",
                kvs=[KVSetRequestKV(key="1", value='{"value_1":"test","value_2":"test2"}', e_tag=5, previous_e_tag=1),
                     KVSetRequestKV(key="2", value='{"value_1":"c","value_2":"test2"}', e_tag=6, previous_e_tag=2),
                     KVSetRequestKV(key="4", value='null', previous_e_tag=4),
                     KVSetRequestKV(key="5", value='{"value_1":"test","value_2":"t2"}')]),
            None)
        self.assertCountEqual(self.kv_store.changed, ["2", "4", "5"])


class KVStoreRPCTestCase(SQLiteTestMixin, RPCServerTestMixin, OpenModuleCoreTestMixin):
    alembic_path = "../tests/test_kv_store_database"
    database_name = "kvstore"
    rpc_channels = ["kv_sync", "rpc-websocket"]

    def setUp(self):
        super().setUp()

        self.rpc_server = RPCServer(self.zmq_context())
        self.kv_handler = KVStoreHandler(self.database, self.core.rpc_client, ExampleKVStore, sync_timeout=2.0)
        self.kv_store = self.kv_handler.stores[0]
        self.kv_handler.register_rpcs(self.rpc_server)
        self.rpc_server.run_as_thread()
        self.wait_for_rpc_server(self.rpc_server)

    def tearDown(self):
        self.rpc_server.shutdown()
        super().tearDown()

    def test_rpcs(self):
        with self.database() as session:
            session.add(ExampleKVEntry(key="test", value_1="test", value_2="test2", e_tag=1))
            session.add(ExampleKVEntry(key="test1", value_1="abc", value_2="def", e_tag=2))
            session.add(ExampleKVEntry(key="test2", value_1="222", value_2="333", e_tag=3))
            session.add(ExampleKVEntry(key="test3", value_1="222", value_2="333", e_tag=4))
            session.commit()
        set_request = KVSetRequest(service=settings.NAME, kvs=[
            KVSetRequestKV(key="test3", value='null', e_tag=5, previous_e_tag=4)])
        self.rpc(channel="kv_sync", type="set", request=set_request, response_type=KVSetResponse)
        sync_request = KVSyncRequest(service=settings.NAME, kvs={
            "test": 1,  # no change
            "test1": 6,  # changed e_tag 2
            "test3": 7,  # no change
        })
        response = self.rpc(channel="kv_sync", type="sync", request=sync_request, response_type=KVSyncResponse)
        self.assertDictEqual(response.additions, {"test2": 3})
        self.assertDictEqual(response.changes, {"test1": 2})
        self.assertDictEqual(response.missing, {"test3": 7})

    def test_filter(self):
        request = KVSetRequest(service="wrong", kvs=[
            KVSetRequestKV(key="test", value="test", e_tag=1, previous_e_tag=0)])
        with self.assertRaises(RPCClient.TimeoutError):
            self.rpc(channel="kv_sync", type="set", request=request, response_type=KVSetResponse, timeout=1)

    def test_start_sync(self):
        def start_sync(*_):
            sync_request = KVSyncRequest(service=settings.NAME, kvs={
                "test": 1,  # no change
                "test1": 5,  # changed e_tag 2
                "test2": 3,  # no change
                "test4": 6  # missing
            })
            sync_response = self.rpc(channel="kv_sync", type="sync", request=sync_request, response_type=KVSyncResponse)
            self.assertDictEqual(sync_response.additions, {"test3": 4})
            self.assertDictEqual(sync_response.changes, {"test1": 2})
            self.assertDictEqual(sync_response.missing, {"test4": 6})
            set_request = KVSetRequest(service=settings.NAME, kvs=[
                KVSetRequestKV(key="test3", value='null', e_tag=5, previous_e_tag=4),
                KVSetRequestKV(key="test4", value='{"value_1": "000", "value_2": "000"}', e_tag=6, previous_e_tag=None),
                KVSetRequestKV(key="test1", value='{"value_1": "789", "value_2": "101"}', e_tag=7, previous_e_tag=2),
            ])
            self.rpc(channel="kv_sync", type="set", request=set_request, response_type=KVSetResponse)
            return ServerSyncResponse()

        with self.database() as session:
            session.add(ExampleKVEntry(key="test", value_1="test", value_2="test2", e_tag=1))  # no change
            session.add(ExampleKVEntry(key="test1", value_1="abc", value_2="def", e_tag=2))  # changed e_tag 5
            session.add(ExampleKVEntry(key="test2", value_1="222", value_2="333", e_tag=3))  # no change
            session.add(ExampleKVEntry(key="test3", value_1="123", value_2="456", e_tag=4))  # addition
            session.commit()

        self.kv_store.rpc_client = MockRPCClient(responses={("rpc-websocket", "server_rpc"): start_sync()})
        conn_id = uuid.uuid4().hex
        self.core.connection_listener.changed(conn_id)
        entry = self.kv_store.sync_with_server()
        self.kv_store._log_sync_rpc_response(entry, conn_id)

    def test_sync_errors(self):
        def raise_error(*_):
            raise ValueError("test")

        def wrong_response(*_):
            return {}

        conn_id = uuid.uuid4().hex

        # status error
        self.core.connection_listener.changed(conn_id)
        self.rpc_server.register_handler("rpc-websocket", "server_rpc", ServerRPCRequest, ServerSyncResponse,
                                         raise_error)
        entry = self.kv_store.sync_with_server()
        with self.assertLogs() as cm:
            success = self.kv_store._log_sync_rpc_response(entry, conn_id)
        self.assertIn("Error on server side in sync", str(cm.output))
        self.assertFalse(success)

        # Un-parseable response
        self.core.connection_listener.changed(conn_id)
        entry = RPCClient.RPCEntry(0)
        entry.response = "test"
        with self.assertLogs() as cm:
            success = self.kv_store._log_sync_rpc_response(entry, conn_id)
        self.assertIn("Unexpected exception in sync response", str(cm.output))
        self.assertFalse(success)

        # timeout
        self.core.connection_listener.changed(conn_id)
        del self.rpc_server.handlers[("rpc-websocket", "server_rpc")]
        entry = self.kv_store.sync_with_server()
        with self.assertLogs() as cm:
            success = self.kv_store._log_sync_rpc_response(entry, conn_id)
        self.assertIn("Timeout syncing kvs", str(cm.output))
        self.assertFalse(success)

    def test_connection_loss_warning(self):
        conn_id = uuid.uuid4().hex
        self.core.connection_listener._process_connection_status(
            ConnectionStatusMessage(connected=ConnectionStatus.online))
        self.core.connection_listener.changed(conn_id)
        self.core.connection_listener._process_connection_status(
            ConnectionStatusMessage(connected=ConnectionStatus.shutdown))
        entry = self.kv_store.sync_with_server()
        with self.assertLogs() as cm:
            success = self.kv_store._log_sync_rpc_response(entry, conn_id)
        self.assertIn("Connection loss during sync", str(cm.output))
        self.assertEqual(len(cm.output), 1)
        self.assertFalse(success)


class KVStoreSyncTriggerTestCase(OpenModuleCoreTestMixin):
    def setUp(self) -> None:
        super().setUp()
        self.rpc_client = MockRPCClient(callbacks={("rpc-websocket", "server_rpc"): self.on_sync_request})
        core().rpc_client = self.rpc_client
        core().connection_listener._set(ConnectionStatus.startup)
        self.kv_handler = KVStoreHandler(None, self.core.rpc_client, ExampleKVStore, sync_timeout=0.5)
        self.kv_store = self.kv_handler.stores[0]
        self.fail = False
        self.errors = False
        self.timeout = 0.0
        self.sync_requested = threading.Event()
        self.sync_count = 0

    def tearDown(self):
        self.kv_handler.shutdown()
        super().tearDown()

    def on_sync_request(self, request: ServerRPCRequest, _):
        """
        test sync request handler
        """
        self.sync_count += 1
        self.sync_requested.set()
        if self.fail:
            raise Exception()
        if self.timeout:
            time.sleep(self.timeout)
            raise TimeoutError()
        return ServerSyncResponse()

    def test_sync_success(self):
        self.kv_handler.run_as_thread()

        self.assertTrue(self.sync_requested.wait(1))  # check sync on start
        self.assertEqual(1, self.sync_count)  # check that only one sync
        self.sync_requested.clear()
        self.assertFalse(self.sync_requested.wait(1))  # check no retry

        core().connection_listener._set(ConnectionStatus.shutdown)
        core().connection_listener._set(ConnectionStatus.startup)
        time.sleep(1)
        self.assertTrue(self.sync_requested.wait(1))  # check sync on going online
        self.sync_requested.clear()
        self.assertFalse(self.sync_requested.wait(1))  # check no second sync
        self.assertEqual(2, self.sync_count)  # check that only one sync additional sync

    def test_sync_fail(self):
        self.fail = True
        self.kv_handler.run_as_thread()

        self.assertTrue(self.sync_requested.wait(1))  # check sync on start
        self.sync_requested.clear()
        self.assertTrue(self.sync_requested.wait(1))  # check retry because of errors

        self.fail = False
        self.timeout = 0.5
        self.sync_requested.clear()
        core().connection_listener._set(ConnectionStatus.shutdown)
        core().connection_listener._set(ConnectionStatus.startup)
        self.assertTrue(self.sync_requested.wait(1))  # check sync on going online

        self.sync_requested.clear()
        self.assertTrue(self.sync_requested.wait(1))  # check retry because of timeout

    def test_shutdown(self):
        self.timeout = 5
        self.kv_store.sync_timeout = 1000
        self.kv_handler.run_as_thread()
        time.sleep(1)
        self.kv_handler.shutdown(2)
        self.assertFalse(self.kv_handler.run_thread.is_alive())

    def test_sync_stop_when_offline(self):
        self.fail = True
        self.kv_handler.run_as_thread()

        self.assertTrue(self.sync_requested.wait(1))  # check sync on start
        self.sync_requested.clear()
        self.assertTrue(self.sync_requested.wait(1))  # check retry because of errors
        core().connection_listener._set(ConnectionStatus.shutdown)
        self.sync_requested.clear()
        self.assertFalse(self.sync_requested.wait(1))  # Stop checking because of offline

    def test_exception_in_run(self):
        def sync_exception(*_):
            raise Exception("test")

        self.kv_store.sync = sync_exception
        with self.assertLogs() as cm:
            self.kv_handler.run_as_thread()
            self.kv_handler.run_thread.join(1)
        self.assertIn("Unexpected exception in KVStore Handler run", str(cm.output))
        self.assertIn("Exception: test", str(cm.output))


class DeprecatedExampleKVEntry(KVEntry, Base):
    __tablename__ = "deprecated_example_kv_entry"

    value: Mapped[str]

    @classmethod
    def parse_value(cls, value: dict) -> dict:
        return value


class DeprecatedExampleKVStore(KVStore):
    database_table = DeprecatedExampleKVEntry


class DeprecatedKVStoreTest(SQLiteTestMixin, OpenModuleCoreTestMixin):
    alembic_path = "../tests/test_kv_store_database"
    database_name = "kvstore"

    def setUp(self):
        super().setUp()
        self.kv_store = DeprecatedExampleKVStore(self.database, self.core.rpc_client)

    def test_deprecation_warning_on_sync(self):
        set_request = KVSetRequest(service=settings.NAME, kvs=[
            KVSetRequestKV(key="test1", value='{"value": "test1"}', e_tag=1),
            KVSetRequestKV(key="test2", value='{"value": "test2"}', e_tag=2),
            KVSetRequestKV(key="test3", value='{"value": "test3"}', e_tag=3),
        ])
        with self.assertWarns(DeprecationWarning):
            self.kv_store.kvs_set(set_request, None)

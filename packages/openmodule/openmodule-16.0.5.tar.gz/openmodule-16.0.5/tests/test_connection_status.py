import datetime
import threading
import time

import freezegun

from openmodule.config import settings
from openmodule.connection_status import ConnectionStatusMessage, ConnectionStatus, \
    BridgeStatus, ConnectionRPCResponse
from openmodule.models.base import OpenModuleModel
from openmodule.rpc import RPCServer
from openmodule.utils.misc_functions import utcnow
from openmodule_test.core import OpenModuleCoreTestMixin
from openmodule_test.rpc import RPCServerTestMixin


class RPCMixin(RPCServerTestMixin, OpenModuleCoreTestMixin):
    current_status = None

    def setUp(self):
        super().setUp()
        self.rpc_server = RPCServer(self.core.context)
        self.rpc_server.register_handler("connection", "status", OpenModuleModel, ConnectionRPCResponse,
                                         self.get_current_status)

        self.rpc_server.run_as_thread()
        self.wait_for_rpc_server(self.rpc_server)

    def tearDown(self) -> None:
        self.rpc_server.shutdown()
        super().tearDown()

    def get_current_status(self, _, __):
        return self.current_status


class ConnectionStatusMixin(OpenModuleCoreTestMixin):
    def setUp(self):
        super().setUp()
        self.connection_listener = self.core.connection_listener

    def dispatch_status(self, connected: ConnectionStatus):
        self.core.messages.dispatch("connection_internal", ConnectionStatusMessage(name="dummy", connected=connected))

    def assert_status(self, status: ConnectionStatus, previous_status: ConnectionStatus):
        self.assertEqual(self.connection_listener._status.connected, status)
        self.assertEqual(self.connection_listener._previous_status.connected, previous_status)

    def assert_bridge_status(self, status: BridgeStatus, previous_status: BridgeStatus):
        self.assertEqual(self.connection_listener._status.bridge_status, status)
        self.assertEqual(self.connection_listener._previous_status.bridge_status, previous_status)


class ConnectionStatusInitialTimeoutTestCase(ConnectionStatusMixin):
    def test_initial_status_timeout(self):
        self.connection_listener.get()
        self.assert_status(ConnectionStatus.shutdown, ConnectionStatus.shutdown)


class ConnectionStatusInitialTest(ConnectionStatusMixin, RPCMixin):
    start_rpc = True

    def test_initial_status_error(self):
        self.current_status = "asdf"
        self.connection_listener.get()
        self.assert_status(ConnectionStatus.shutdown, ConnectionStatus.shutdown)

    def test_online_on_start(self):
        self.current_status = ConnectionRPCResponse(connected=ConnectionStatus.online)
        self.connection_listener.get()
        self.assert_status(ConnectionStatus.online, ConnectionStatus.shutdown)

    def test_offline_on_start(self):
        self.current_status = ConnectionRPCResponse(connected=ConnectionStatus.offline)
        self.connection_listener.get()
        self.assert_status(ConnectionStatus.offline, ConnectionStatus.shutdown)

    def test_shutdown_on_start(self):
        self.current_status = ConnectionRPCResponse(connected=ConnectionStatus.shutdown)
        self.connection_listener.get()
        self.assert_status(ConnectionStatus.shutdown, ConnectionStatus.shutdown)


class NoConnectionMessagesTestCase(ConnectionStatusMixin, RPCMixin):
    current_status = dict(connected="online")

    def setUp(self):
        super().setUp()
        self.connection_listener._run_sleep_time = 0.01

    def test_no_message(self):
        self.connection_listener.get()
        self.assert_status(ConnectionStatus.online, ConnectionStatus.shutdown)
        with freezegun.freeze_time(utcnow() + datetime.timedelta(seconds=10)):
            self.connection_listener.check_timeout()
        self.assert_status(ConnectionStatus.online, ConnectionStatus.shutdown)
        with freezegun.freeze_time(utcnow() + datetime.timedelta(seconds=61)):
            self.connection_listener.check_timeout()
        self.assert_status(ConnectionStatus.shutdown, ConnectionStatus.online)
        self.connection_listener._set(ConnectionStatus.online)
        self.assert_status(ConnectionStatus.online, ConnectionStatus.shutdown)
        with freezegun.freeze_time(utcnow() + datetime.timedelta(seconds=500)):
            self.connection_listener.check_timeout()
        self.assert_status(ConnectionStatus.shutdown, ConnectionStatus.online)

    def test_check_on_get(self):
        self.connection_listener.get()
        self.assert_status(ConnectionStatus.online, ConnectionStatus.shutdown)
        with freezegun.freeze_time(utcnow() + datetime.timedelta(seconds=10)):
            self.connection_listener.get()
        self.assert_status(ConnectionStatus.online, ConnectionStatus.shutdown)
        with freezegun.freeze_time(utcnow() + datetime.timedelta(seconds=61)):
            self.connection_listener.get()
        self.assert_status(ConnectionStatus.shutdown, ConnectionStatus.online)
        self.connection_listener._set(ConnectionStatus.online)
        self.assert_status(ConnectionStatus.online, ConnectionStatus.shutdown)
        with freezegun.freeze_time(utcnow() + datetime.timedelta(seconds=500)):
            self.connection_listener.get()
        self.assert_status(ConnectionStatus.shutdown, ConnectionStatus.online)

    def test_stay_offline(self):
        self.connection_listener.get()
        self.connection_listener._set(ConnectionStatus.offline)
        self.assert_status(ConnectionStatus.offline, ConnectionStatus.online)
        with freezegun.freeze_time(utcnow() + datetime.timedelta(seconds=80)):
            self.connection_listener.check_timeout()
        self.assert_status(ConnectionStatus.offline, ConnectionStatus.online)

    def test_shutdown_after_startup(self):
        self.connection_listener.get()
        self.connection_listener._set(ConnectionStatus.startup)
        self.assert_status(ConnectionStatus.startup, ConnectionStatus.online)
        with freezegun.freeze_time(utcnow() + datetime.timedelta(seconds=80)):
            self.connection_listener.check_timeout()
        self.assert_status(ConnectionStatus.shutdown, ConnectionStatus.startup)


class InternalRunTestCase(ConnectionStatusMixin):
    def wait_for_status(self, status: ConnectionStatus, timeout: float = 3):
        start = time.time()
        while time.time() - start < timeout:
            if self.connection_listener._status.connected == status:
                return
            time.sleep(0.02)
        raise TimeoutError("Timeout waiting for status to change to {}".format(status))

    def dispatch_status(self, connected: ConnectionStatus):
        self.core.publish(ConnectionStatusMessage(name=settings.NAME, connected=connected), "connection_internal")

    def test_internal_run(self):
        self.connection_listener.get()
        self.assertEqual(self.connection_listener._status.connected, ConnectionStatus.shutdown)
        self.assertEqual(self.connection_listener._previous_status.connected, ConnectionStatus.shutdown)
        self.dispatch_status(ConnectionStatus.online)
        self.wait_for_status(ConnectionStatus.online)
        self.assertEqual(self.connection_listener._previous_status.connected, ConnectionStatus.shutdown)
        with freezegun.freeze_time(utcnow() + datetime.timedelta(seconds=61)):
            status = self.connection_listener.get()
            self.assertEqual(status, ConnectionStatus.shutdown)
        self.assertEqual(self.connection_listener._previous_status.connected, ConnectionStatus.online)
        self.dispatch_status(ConnectionStatus.offline)
        self.wait_for_status(ConnectionStatus.offline)
        self.assertEqual(self.connection_listener._previous_status.connected, ConnectionStatus.shutdown)

    def test_changed_condition(self):
        def dispatch_after_time():
            time.sleep(0.1)
            self.dispatch_status(ConnectionStatus.online)

        self.connection_listener.get()
        self.assertEqual(self.connection_listener._status.connected, ConnectionStatus.shutdown)
        threading.Thread(target=dispatch_after_time).start()
        self.assertTrue(self.connection_listener.wait_for_change(timeout=3))
        self.assertEqual(self.connection_listener._status.connected, ConnectionStatus.online)
        threading.Thread(target=dispatch_after_time).start()
        self.assertFalse(self.connection_listener.wait_for_change(timeout=1))


class ConditionTest(ConnectionStatusMixin):
    def test_multiple_wait(self):
        self.oks = []
        self.connection_listener._set(ConnectionStatus.online)
        for i in range(2):
            threading.Thread(target=self.waiter).start()
        time.sleep(1)
        self.connection_listener._set(ConnectionStatus.shutdown)
        time.sleep(1)
        self.assertEqual(2, len(self.oks))

    def waiter(self):
        if not self.connection_listener.wait_for_change(3):
            return
        if self.connection_listener.get() != ConnectionStatus.shutdown:
            return
        self.oks.append(True)



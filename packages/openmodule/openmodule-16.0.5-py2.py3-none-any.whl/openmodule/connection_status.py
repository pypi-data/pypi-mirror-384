import logging
import threading
import time
from enum import StrEnum

from openmodule import sentry
from openmodule.dispatcher import MessageDispatcher
from openmodule.models.base import ZMQMessage, OpenModuleModel


class ConnectionStatus(StrEnum):
    startup = "startup"
    online = "online"
    shutdown = "shutdown"
    offline = "offline"


class BridgeStatus(StrEnum):
    online = "online"
    offline = "offline"


class ConnectionStatusMessage(ZMQMessage):
    connected: ConnectionStatus
    bridge_status: BridgeStatus | None = None
    type: str = "connection_status"


class ConnectionRPCResponse(OpenModuleModel):
    connected: ConnectionStatus
    bridge_status: BridgeStatus | None = None


class ConnectionStatusListener:
    def __init__(self, dispatcher: MessageDispatcher, rpc_client):
        self._log = logging.getLogger(self.__class__.__name__)
        self._status: ConnectionRPCResponse | None = None
        self._previous_status: ConnectionRPCResponse = ConnectionRPCResponse(connected=ConnectionStatus.shutdown)
        self._changed = threading.Condition(threading.Lock())
        self.last_changed_time = 0.0
        self._status_lock = threading.Lock()
        self._last_message = time.time()
        self.rpc_client = rpc_client
        self._listener = dispatcher.register_handler("connection_internal", ConnectionStatusMessage,
                                                     self._process_connection_status)
        self._got_change_ids: set[str] = set()
        self._got_change_ids_lock = threading.Lock()

    def wait_for_change(self, timeout: float = None) -> bool:
        """Returns true when the connection status changes, otherwise waits for the timeout (or infinitely if none)
        and returns false."""
        with self._changed:
            res = self._changed.wait(timeout)
            return res

    def changed(self, id: str):
        if self._status is None:  # make sure status is initialized before we check for changed
            self.get_current_status()
        with self._got_change_ids_lock:
            changed = id not in self._got_change_ids
            self._got_change_ids.add(id)
        return changed

    @property
    def previous(self) -> ConnectionStatus:
        return self._previous_status.connected

    @property
    def previous_bridge(self) -> BridgeStatus:
        return self._previous_status.bridge_status

    def get(self) -> ConnectionStatus:
        """Checks if the last message was less then a minute ago and returns the current connection status."""
        if self._status:
            self.check_timeout()
            return self._status.connected
        else:
            self.get_current_status()
            return self._status.connected

    def get_bridge(self) -> BridgeStatus:
        """Checks if the last message was less then a minute ago and returns the current bridge status."""
        if self._status:
            self.check_timeout()
            return self._status.bridge_status
        else:
            self.get_current_status()
            return self._status.bridge_status

    def check_timeout(self) -> None:
        """Checks if the last message was less then a minute ago"""

        with self._status_lock:
            if not self._status:
                return
            if self._status.connected not in (ConnectionStatus.shutdown, ConnectionStatus.offline) and \
                    time.time() - self._last_message > 1 * 60:
                self._log.debug("Connection status message timeout")
                self._set(ConnectionStatus.shutdown)

    @sentry.trace
    def get_current_status(self) -> ConnectionRPCResponse:
        """Checks the current_status by sending an RPC to om_rpc_client"""
        try:
            connection_status = self.rpc_client.rpc("connection", "status", OpenModuleModel(), ConnectionRPCResponse)
            with self._status_lock:
                self._last_message = time.time()
                self._set(connection_status.connected, connection_status.bridge_status)
                return self._status
        except Exception as e:
            self._log.warning(f"Could not get initial connection status because of {e.__class__.__name__}")
            with self._status_lock:
                self._previous_status = ConnectionRPCResponse(connected=ConnectionStatus.shutdown)
                self._status = ConnectionRPCResponse(connected=ConnectionStatus.shutdown)
                return self._status

    def _set(self, status: ConnectionStatus, bridge_status: BridgeStatus | None = None):
        if not self._status or status != self._status.connected or \
                (bridge_status and bridge_status != self._status.bridge_status):
            self._previous_status = self._status or self._previous_status  # initial status is None
            bridge_status = (bridge_status or self._status.bridge_status) if self._status else bridge_status
            self._status = ConnectionRPCResponse(connected=status, bridge_status=bridge_status)
            with self._changed:
                self._log.info(f"Connection Status Changed: internet: {status}, bridge: {bridge_status}")
                self.last_changed_time = time.time()
                with self._got_change_ids_lock:
                    self._got_change_ids.clear()
                self._changed.notify_all()

    def _process_connection_status(self, message: ConnectionStatusMessage) -> None:
        """Forwards the current connection status of the om_rpc_client"""
        with self._status_lock:
            self._last_message = time.time()
            self._set(message.connected, message.bridge_status)

import logging
import threading
from enum import StrEnum
from typing import Callable

import zmq
from openmodule.dispatcher import MessageDispatcher
from openmodule.models.signals import SignalMessage, SignalType, GetSignalValueRequest, GetSignalValueResponse, \
    TriggerSignalsRequest, TriggerSignalsResponse
from openmodule.rpc import RPCClient


class ChangeType(StrEnum):
    rising_edge = "rising_edge"  # value changed from 0 to 1
    falling_edge = "falling_edge"  # value change from 1 to 0
    data_change = "data_change"  # value is 1, additional data is set and no rising_edge
    none = "none"  # value unchanged and not data_change


class FilterType(StrEnum):
    rising_edge = "rising_edge"  # only rising edges
    falling_edge = "falling_edge"  # only falling edges
    any_edge = "any_edge"  # rising and falling edges
    data_change = "data_change"  # all messages with value true (including rising edges) and additional_data set
    any_change = "any_change"  # rising and falling edges and additional_data changes
    any = "any"  # no filtering of changes (also when nothing changes)

    def matches_change(self, change_type: ChangeType) -> bool:
        if self.value == FilterType.rising_edge:
            return change_type == ChangeType.rising_edge
        elif self.value == FilterType.falling_edge:
            return change_type == ChangeType.falling_edge
        elif self.value == FilterType.any_edge:
            return change_type in [ChangeType.rising_edge, ChangeType.falling_edge]
        elif self.value == FilterType.data_change:
            return change_type in [ChangeType.rising_edge, ChangeType.data_change]
        elif self.value == FilterType.any_change:
            return change_type != ChangeType.none
        elif self.value == FilterType.any:
            return True
        else:
            raise TypeError("unknown change type")


class Signal:
    def __init__(self, signal_message: SignalMessage, change_type: ChangeType):
        self.signal: str = signal_message.signal
        self.type: SignalType = signal_message.type
        self.value: bool = signal_message.value
        self.additional_data: dict | None = signal_message.additional_data
        self.gate: str | None = signal_message.gate
        self.parking_area_id: str | None = signal_message.parking_area_id
        self.change_type: ChangeType = change_type


class Listener:
    def __init__(self, signal_name: str, filter_type: FilterType, callback: Callable[[Signal], None],
                 tag: str | None):
        self.signal_name: str = signal_name
        self.filter_type: FilterType = filter_type
        self.callback: Callable[[Signal], None] = callback
        self.tag: str | None = tag

    def matches(self, signal_name: str, change_type: ChangeType) -> bool:
        return self.signal_name == signal_name and self.filter_type.matches_change(change_type)


class SignalListener:
    def __init__(self, dispatcher: MessageDispatcher, rpc_client: RPCClient):
        assert not dispatcher.is_multi_threaded, (
            "you cannot use a multithreaded message dispatcher for the SignalListener. It is highly reliant "
            "on receiving messages in the correct order!"
        )
        self.current_states: dict[str, tuple[bool, dict | None]] = dict()
        self.listeners: list[Listener] = list()
        self.listeners_lock = threading.Lock()
        self.log = logging.getLogger(self.__class__.__name__)
        self.rpc_client = rpc_client
        dispatcher.register_handler("signal", SignalMessage, self._on_signal_message, match_type=False)

    def add_listener(self, signal_name: str, filter_type: FilterType, callback: Callable[[Signal], None],
                     tag: str | None):
        """
        Calls the given callback method whenever a signal message is received and the circumstances fulfill the given
        filter_type
        :param signal_name: signal name that needs to experience a rising edge to call the callback
        :param filter_type: One of the available FilterType
        :param callback: the function that is called when a rising edge occurs on listen_to
        :param tag: a tag to group listeners for later removal
        """
        with self.listeners_lock:
            self.listeners.append(Listener(signal_name, filter_type, callback, tag))

    def remove_listener(self, tag: str | None = None):
        """
        :param tag: all listeners with this tag are removed. If no tag is given, all listeners are removed
        """
        with self.listeners_lock:
            self.listeners = [listener for listener in self.listeners if tag is not None and listener.tag != tag]

    def get_value(self, signal_name: str) -> bool:
        """
        returns the current value of a signal.
        If no value is available yet, it will be requested via rpc.
        If no answer to RPC, log exception/error and return False
        :param signal_name: Name of signal to get value from
        """
        return self.get_value_and_additional_data(signal_name)[0]

    def get_value_and_additional_data(self, signal_name: str) -> tuple[bool, dict | None]:
        """
        returns the current value of a signal including additional_data.
        If no value is available yet, it will be requested via rpc.
        If no answer to RPC, log exception/error and return (False, None)
        :param signal_name: Name of signal to get value from
        """
        if signal_name not in self.current_states:
            try:
                res: GetSignalValueResponse = self.rpc_client.rpc(
                    "signal", "get_value", GetSignalValueRequest(signal=signal_name),
                    GetSignalValueResponse, timeout=1.0)
                self.current_states[signal_name] = (res.value, res.additional_data)
            except RPCClient.Exception:
                self.log.exception("Error while getting signal value. Assuming False.")
                self.current_states[signal_name] = (False, None)

        return self.current_states[signal_name]

    def trigger_signals(self, tag: str | None = None, timeout: float = 3.0) -> bool:
        """
        :param tag: if given, only signals of listeners with given tag are triggered
        :param timeout: timeout for trigger RPC. Default is 3.0
        """
        try:
            with self.listeners_lock:
                if tag is None:
                    signals_to_trigger = list({l.signal_name for l in self.listeners})
                else:
                    signals_to_trigger = list({l.signal_name for l in self.listeners if l.tag == tag})
            res: TriggerSignalsResponse = self.rpc_client.rpc(
                "signal", "trigger_signals", TriggerSignalsRequest(signals=signals_to_trigger),
                TriggerSignalsResponse, timeout
            )
            if not res.success:
                self.log.error("Failed to trigger all registered signals.")
            return res.success
        except RPCClient.Exception:
            self.log.exception("Error while triggering signals.")
            return False

    def _on_signal_message(self, message: SignalMessage):
        """
        This handler receives all IO Messages, saves any changes and calls any listeners registered in the IoListener
        """
        old_state = self.current_states.get(message.signal)
        old_value = old_state and old_state[0]  # only value without additional_data
        self.current_states[message.signal] = (message.value, message.additional_data)
        if old_value != message.value and message.value:
            change_type = ChangeType.rising_edge
        elif old_value != message.value:
            change_type = ChangeType.falling_edge
        elif message.value and message.additional_data:
            change_type = ChangeType.data_change
        else:
            change_type = ChangeType.none
        with self.listeners_lock:
            for listener in self.listeners:
                """
                Handles the registered listeners the same as the dispatcher.
                Is copied here because all messages are needed to keep current_states up to date.
                """
                if listener.matches(message.signal, change_type):
                    try:
                        listener.callback(Signal(message, change_type))
                    except zmq.ContextTerminated:
                        raise
                    except Exception:
                        self.log.exception("Error in signal callback")

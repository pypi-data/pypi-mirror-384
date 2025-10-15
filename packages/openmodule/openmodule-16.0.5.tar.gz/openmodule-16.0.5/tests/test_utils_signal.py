from openmodule.models.signals import SignalMessage, SignalType, TriggerSignalsRequest, TriggerSignalsResponse
from openmodule.rpc import RPCClient
from openmodule.utils.signal_listener import (SignalListener, GetSignalValueRequest, GetSignalValueResponse, FilterType,
                                              ChangeType, Signal)
from openmodule_test.core import OpenModuleCoreTestMixin
from openmodule_test.eventlistener import MockEvent
from openmodule_test.rpc import MockRPCClient


class TestSignalListener(OpenModuleCoreTestMixin):
    def test_message_parsing(self):
        msg = SignalMessage.model_validate({
            "type": "open",
            "value": True,
            "gate": "gate",
            "signal": "gate-open",
            "additional_data": {
                "a": "b"
            }
        })
        self.assertIs("open", msg.type)
        msg = SignalMessage.model_validate({
            "type": "something_new",
            "value": True,
            "gate": "gate",
            "signal": "gate-open"
        })
        self.assertIs("something_new", msg.type)

    def test_add_and_remove(self):
        signal_listener = SignalListener(self.core.messages, self.core.rpc_client)
        on_rising_edge = MockEvent()
        on_falling_edge = MockEvent()
        on_any_edge = MockEvent()
        on_data_change = MockEvent()
        on_any_change = MockEvent()
        on_any = MockEvent()

        signal_listener.add_listener("signal_name", FilterType.rising_edge, on_rising_edge, "tag")
        signal_listener.add_listener("signal_name", FilterType.falling_edge, on_falling_edge, "tag")
        signal_listener.add_listener("signal_name", FilterType.any_edge, on_any_edge, "tag")
        signal_listener.add_listener("signal_name", FilterType.data_change, on_data_change, "tag2")
        signal_listener.add_listener("signal_name", FilterType.any_change, on_any_change, "tag2")
        signal_listener.add_listener("signal_name", FilterType.any, on_any, "tag3")

        self.assertEqual(6, len(signal_listener.listeners))

        signal_listener.remove_listener("tag")
        self.assertEqual(3, len(signal_listener.listeners))
        self.assertEqual("tag2", signal_listener.listeners[0].tag)
        self.assertEqual("tag2", signal_listener.listeners[1].tag)
        self.assertEqual("tag3", signal_listener.listeners[2].tag)

        signal_listener.remove_listener()
        self.assertEqual(0, len(signal_listener.listeners))

    def test_filtering_and_signal_data(self):
        signal_listener = SignalListener(self.core.messages, self.core.rpc_client)
        signal_listener._on_signal_message(SignalMessage(type=SignalType.custom, value=False,
                                                         signal="signal1"))

        on_signal1 = MockEvent()
        on_signal2 = MockEvent()
        signal_listener.add_listener("signal1", FilterType.any, on_signal1, "tag")
        signal_listener.add_listener("signal2", FilterType.any, on_signal2, "tag")

        signal_listener._on_signal_message(SignalMessage(type=SignalType.custom, value=True, signal="signal1",
                                                         additional_data={"a": "b"}, parking_area_id="pa1", gate="g1"))
        self.assertEqual(1, on_signal1.call_count)
        signal: Signal = on_signal1.call_args[0][0]
        self.assertEqual("signal1", signal.signal)
        self.assertEqual(SignalType.custom, signal.type)
        self.assertEqual(True, signal.value)
        self.assertEqual({"a": "b"}, signal.additional_data)
        self.assertEqual("g1", signal.gate)
        self.assertEqual("pa1", signal.parking_area_id)
        on_signal1.reset_mock()
        self.assertEqual(0, on_signal2.call_count)
        on_signal2.reset_mock()

        signal_listener._on_signal_message(SignalMessage(type=SignalType.custom, value=True, signal="signal4"))
        self.assertEqual(0, on_signal1.call_count)
        on_signal1.reset_mock()
        self.assertEqual(0, on_signal2.call_count)
        on_signal2.reset_mock()

    def test_changes(self):
        signal_listener = SignalListener(self.core.messages, self.core.rpc_client)
        on_rising_edge = MockEvent()
        on_falling_edge = MockEvent()
        on_any_edge = MockEvent()
        on_data_change = MockEvent()
        on_any_change = MockEvent()
        on_any = MockEvent()

        signal_listener.add_listener("signal_name", FilterType.rising_edge, on_rising_edge, "tag")
        signal_listener.add_listener("signal_name", FilterType.falling_edge, on_falling_edge, "tag")
        signal_listener.add_listener("signal_name", FilterType.any_edge, on_any_edge, "tag")
        signal_listener.add_listener("signal_name", FilterType.data_change, on_data_change, "tag2")
        signal_listener.add_listener("signal_name", FilterType.any_change, on_any_change, "tag2")
        signal_listener.add_listener("signal_name", FilterType.any, on_any, "tag3")

        # rising edge
        signal_listener._on_signal_message(SignalMessage(type=SignalType.custom, value=True, signal="signal_name"))
        self.assertEqual(1, on_rising_edge.call_count)
        self.assertEqual(ChangeType.rising_edge, on_rising_edge.call_args[0][0].change_type)
        on_rising_edge.reset_mock()
        self.assertEqual(0, on_falling_edge.call_count)
        on_falling_edge.reset_mock()
        self.assertEqual(1, on_any_edge.call_count)
        self.assertEqual(ChangeType.rising_edge, on_any_edge.call_args[0][0].change_type)
        on_any_edge.reset_mock()
        self.assertEqual(1, on_data_change.call_count)
        self.assertEqual(ChangeType.rising_edge, on_data_change.call_args[0][0].change_type)
        on_data_change.reset_mock()
        self.assertEqual(1, on_any_change.call_count)
        self.assertEqual(ChangeType.rising_edge, on_any_change.call_args[0][0].change_type)
        on_any_change.reset_mock()
        self.assertEqual(1, on_any.call_count)
        self.assertEqual(ChangeType.rising_edge, on_any.call_args[0][0].change_type)
        on_any.reset_mock()

        # no change
        signal_listener._on_signal_message(SignalMessage(type=SignalType.custom, value=True, signal="signal_name"))
        self.assertEqual(0, on_rising_edge.call_count)
        on_rising_edge.reset_mock()
        self.assertEqual(0, on_falling_edge.call_count)
        on_falling_edge.reset_mock()
        self.assertEqual(0, on_any_edge.call_count)
        on_any_edge.reset_mock()
        self.assertEqual(0, on_data_change.call_count)
        on_data_change.reset_mock()
        self.assertEqual(0, on_any_change.call_count)
        on_any_change.reset_mock()
        self.assertEqual(1, on_any.call_count)
        self.assertEqual(ChangeType.none, on_any.call_args[0][0].change_type)
        on_any.reset_mock()

        # additional_data change
        signal_listener._on_signal_message(SignalMessage(type=SignalType.custom, value=True, signal="signal_name",
                                                         additional_data={"a": "b"}))
        self.assertEqual(0, on_rising_edge.call_count)
        on_rising_edge.reset_mock()
        self.assertEqual(0, on_falling_edge.call_count)
        on_falling_edge.reset_mock()
        self.assertEqual(0, on_any_edge.call_count)
        on_any_edge.reset_mock()
        self.assertEqual(1, on_data_change.call_count)
        self.assertEqual(ChangeType.data_change, on_data_change.call_args[0][0].change_type)
        on_data_change.reset_mock()
        self.assertEqual(1, on_any_change.call_count)
        self.assertEqual(ChangeType.data_change, on_any_change.call_args[0][0].change_type)
        on_any_change.reset_mock()
        self.assertEqual(1, on_any.call_count)
        self.assertEqual(ChangeType.data_change, on_any.call_args[0][0].change_type)
        on_any.reset_mock()

        # falling edge
        signal_listener._on_signal_message(SignalMessage(type=SignalType.custom, value=False, signal="signal_name"))
        self.assertEqual(0, on_rising_edge.call_count)
        on_rising_edge.reset_mock()
        self.assertEqual(1, on_falling_edge.call_count)
        self.assertEqual(ChangeType.falling_edge, on_falling_edge.call_args[0][0].change_type)
        on_falling_edge.reset_mock()
        self.assertEqual(1, on_any_edge.call_count)
        self.assertEqual(ChangeType.falling_edge, on_any_edge.call_args[0][0].change_type)
        on_any_edge.reset_mock()
        self.assertEqual(0, on_data_change.call_count)
        on_data_change.reset_mock()
        self.assertEqual(1, on_any_change.call_count)
        self.assertEqual(ChangeType.falling_edge, on_any_change.call_args[0][0].change_type)
        on_any_change.reset_mock()
        self.assertEqual(1, on_any.call_count)
        self.assertEqual(ChangeType.falling_edge, on_any.call_args[0][0].change_type)
        on_any.reset_mock()

    def test_get(self):
        def get_value(req: GetSignalValueRequest, _) -> bool:
            if req.signal == "true":
                return GetSignalValueResponse(value=True, additional_data={"a": "b"})
            if req.signal == "false":
                return GetSignalValueResponse(value=False)
            elif req.signal == "exception":
                raise RPCClient.TimeoutError

        rpc_client = MockRPCClient(immediate_callbacks={("signal", "get_value"): get_value})
        signal_listener = SignalListener(self.core.messages, rpc_client)
        self.assertEqual(True, signal_listener.get_value("true"))
        self.assertEqual(False, signal_listener.get_value("false"))
        self.assertEqual((True, {"a": "b"}), signal_listener.get_value_and_additional_data("true"))
        self.assertEqual((False, None), signal_listener.get_value_and_additional_data("false"))
        with self.assertLogs() as log:
            self.assertEqual(False, signal_listener.get_value("exception"))
        self.assertIn("Error while getting signal value. Assuming False", str(log.output))

        # test no rpc if message was processed
        signal_listener._on_signal_message(SignalMessage(type=SignalType.custom, value=True, signal="false"))
        self.assertEqual(True, signal_listener.get_value("false"))

    def test_trigger(self):
        request: TriggerSignalsRequest | None = None
        res = TriggerSignalsResponse(success=True)
        def trigger(req: TriggerSignalsRequest, _) -> bool:
            nonlocal request, res
            request = req
            if res is None:
                raise RPCClient.TimeoutError
            else:
                return res

        rpc_client = MockRPCClient(immediate_callbacks={("signal", "trigger_signals"): trigger})
        signal_listener = SignalListener(self.core.messages, rpc_client)
        on_rising_edge = MockEvent()
        on_falling_edge = MockEvent()
        on_any_edge = MockEvent()
        on_data_change = MockEvent()
        on_any_change = MockEvent()
        on_any = MockEvent()

        signal_listener.add_listener("1", FilterType.rising_edge, on_rising_edge, "tag")
        signal_listener.add_listener("1", FilterType.falling_edge, on_falling_edge, "tag")
        signal_listener.add_listener("2", FilterType.any_edge, on_any_edge, "tag")
        signal_listener.add_listener("3", FilterType.data_change, on_data_change, "tag2")
        signal_listener.add_listener("4", FilterType.any_change, on_any_change, "tag2")
        signal_listener.add_listener("5", FilterType.any, on_any, "tag3")

        signal_listener.trigger_signals()
        self.assertCountEqual(["1", "2", "3", "4", "5"], request.signals)

        signal_listener.trigger_signals("tag")
        self.assertCountEqual(["1", "2"], request.signals)

        res = TriggerSignalsResponse(success=False)
        with self.assertLogs() as log:
            self.assertEqual(False, signal_listener.trigger_signals())
        self.assertIn("Failed to trigger all registered signals.", str(log.output))

        res = None
        with self.assertLogs() as log:
            self.assertEqual(False, signal_listener.trigger_signals())
        self.assertIn("Error while triggering signals.", str(log.output))

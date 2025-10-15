import time
from datetime import datetime
from functools import partial
from unittest import TestCase

import freezegun
import orjson
from settings_models.settings.common import Gate

from openmodule.dispatcher import MessageDispatcher
from openmodule.models.base import Direction, Gateway
from openmodule.models.presence import PresenceBaseMessage, PresenceRPCResponse, PresenceBaseData, PresenceMedia, \
    PresenceRPCRequest, PresenceEnterMessage, PresenceLeaveMessage
from openmodule.models.vehicle import MakeModel, LPRMedium, PresenceAllIds, EnterDirection
from openmodule.utils.presence import PresenceListener
from openmodule.utils.misc_functions import utcnow
from openmodule_test.core import OpenModuleCoreTestMixin
from openmodule_test.eventlistener import MockEvent
from openmodule_test.presence import PresenceSimulator
from openmodule_test.rpc import MockRPCClient
from openmodule_test.settings import SettingsMocker


class PresenceMessageTest(TestCase):
    def test_enter_time_default(self):
        msg = PresenceEnterMessage.model_validate({
            "all_ids": {
                "lpr": [
                    {
                        "alternatives": [
                            {
                                "confidence": 0.20645777329012063,
                                "plate": "K 510 BV"
                            }
                        ],
                        "confidence": 0.20645777329012063,
                        "country": {
                            "code": "A",
                            "confidence": 0.9156234893865384,
                            "state": "K"
                        },
                        "id": "K 510 BV",
                        "no_countrylogic_id": "K 510 BV",
                        "track_id": 1700560556852837123,
                        "type": "lpr"
                    }
                ]
            },
            "enter_direction": "forward",
            "gateway": {
                "direction": "in",
                "gate": "einfahrt"
            },
            "last_update": 1700560557.237208,
            "make_model": {
                "make": "UNKNOWN",
                "make_confidence": -1.0,
                "model": "UNKNOWN",
                "model_confidence": -1.0
            },
            "medium": {
                "lpr": {
                    "alternatives": [
                        {
                            "confidence": 0.20645777329012063,
                            "plate": "K 510 BV"
                        }
                    ],
                    "changed": False,
                    "confidence": 0.20645777329012063,
                    "country": {
                        "code": "A",
                        "confidence": 0.9156234893865384,
                        "state": "K"
                    },
                    "id": "K 510 BV",
                    "no_countrylogic_id": "K 510 BV",
                    "track_id": 1700560556852837123,
                    "type": "lpr"
                }
            },
            "name": "enter-om_alpr_tracking_2",
            "present-area-name": "einfahrt",
            "source": "einfahrt",
            "timestamp": 1700560557.237477,
            "type": "enter",
            "vehicle_id": 1700560557231782099
        })
        self.assertEqual(datetime(2023, 11, 21, 9, 55, 57, 231782), msg.enter_time)

    def test_leave_time_default(self):
        msg = PresenceLeaveMessage.model_validate({
            "all_ids": {
                "lpr": [
                    {
                        "alternatives": [
                            {
                                "confidence": 0.20645777329012063,
                                "plate": "K 510 BV"
                            }
                        ],
                        "confidence": 0.20645777329012063,
                        "country": {
                            "code": "A",
                            "confidence": 0.9156234893865384,
                            "state": "K"
                        },
                        "id": "K 510 BV",
                        "no_countrylogic_id": "K 510 BV",
                        "track_id": 1700560556852837123,
                        "type": "lpr"
                    }
                ]
            },
            "enter_direction": "forward",
            "num-presents": 0,
            "gateway": {
                "direction": "in",
                "gate": "einfahrt"
            },
            "last_update": 1700560557.237208,
            "make_model": {
                "make": "UNKNOWN",
                "make_confidence": -1.0,
                "model": "UNKNOWN",
                "model_confidence": -1.0
            },
            "medium": {
                "lpr": {
                    "alternatives": [
                        {
                            "confidence": 0.20645777329012063,
                            "plate": "K 510 BV"
                        }
                    ],
                    "changed": False,
                    "confidence": 0.20645777329012063,
                    "country": {
                        "code": "A",
                        "confidence": 0.9156234893865384,
                        "state": "K"
                    }, 
                    "id": "K 510 BV",
                    "no_countrylogic_id": "K 510 BV",
                    "track_id": 1700560556852837123,
                    "type": "lpr"
                }
            },
            "name": "leave-om_alpr_tracking_2",
            "present-area-name": "einfahrt", 
            "source": "einfahrt",
            "timestamp": 1700560557.231782,
            "type": "leave", 
            "vehicle_id": 1700560557231782099
        })
        self.assertEqual(datetime(2023, 11, 21, 9, 55, 57, 231782), msg.leave_time)


class BasePresenceTest(TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.dispatcher = MessageDispatcher()
        self.presence_sim = PresenceSimulator("gate_in", Direction.IN,
                                              lambda x: self.dispatcher.dispatch("presence", x))

        self.presence = PresenceListener(self.dispatcher)
        self.on_enter = MockEvent()
        self.on_forward = MockEvent()
        self.on_backward = MockEvent()
        self.on_change = MockEvent()
        self.on_leave = MockEvent()
        self.presence.on_enter.append(self.on_enter)
        self.presence.on_forward.append(self.on_forward)
        self.presence.on_backward.append(self.on_backward)
        self.presence.on_change.append(self.on_change)
        self.presence.on_leave.append(self.on_leave)


class PresenceTest(BasePresenceTest):
    def test_cannot_use_present_vehicle_without_gate(self):
        with self.assertRaises(AssertionError) as e:
            self.presence.present_vehicle.json()
        self.assertIn("please access the present vehicle per gate", str(e.exception))

        self.presence.gate = "test"
        val = self.presence.present_vehicle
        self.assertIsNone(val)

    def test_double_entry(self):
        self.presence_sim.enter(self.presence_sim.vehicle().lpr("A", "G ARIVO1"))
        self.on_enter.wait_for_call()
        self.assertEqual("G ARIVO1", self.presence.present_vehicles["gate_in"].lpr.id)

        MockEvent.reset_all_mocks()
        self.presence_sim.current_present = None
        with self.assertLogs() as cm:
            self.presence_sim.enter(self.presence_sim.vehicle().lpr("A", "G ARIVO2"))
            self.on_enter.wait_for_call()
            self.on_leave.wait_for_call()
        self.assertEqual("G ARIVO2", self.presence.present_vehicles["gate_in"].lpr.id)
        self.assertIn("A leave will be faked", str(cm))

    def test_faulty_exit(self):
        with self.assertLogs() as cm:
            self.presence_sim.current_present = self.presence_sim.vehicle().lpr("A", "G ARIVO1")
            self.presence_sim.leave()
            time.sleep(1)
            self.assertEqual({}, self.presence.present_vehicles)
        self.assertIn("The leave will be ignored", str(cm))

        self.presence_sim.enter(self.presence_sim.vehicle().lpr("A", "G ARIVO1"))
        self.on_enter.wait_for_call()
        self.assertEqual("G ARIVO1", self.presence.present_vehicles["gate_in"].lpr.id)

        self.presence_sim.current_present = self.presence_sim.vehicle().lpr("A", "G ARIVO2")
        with self.assertLogs() as cm:
            self.presence_sim.leave()
            self.on_leave.wait_for_call()
            self.assertEqual({}, self.presence.present_vehicles)
        self.assertIn("We are fake-leaving the currently present vehicle", str(cm))

    def test_vehicle_id_change(self):
        vehicle_0 = self.presence_sim.vehicle()
        self.presence_sim.enter(vehicle_0)
        self.on_enter.wait_for_call()
        self.assertEqual(vehicle_0.vehicle_id, self.presence.present_vehicles["gate_in"].id)
        self.on_enter.reset_mock()

        vehicle_1 = self.presence_sim.vehicle().lpr("A", "G ARIVO1")
        self.presence_sim.change_vehicle_and_id(vehicle_1)
        self.on_leave.wait_for_call()
        self.on_enter.wait_for_call()

        self.assertEqual(vehicle_1.vehicle_id, self.presence.present_vehicles["gate_in"].id)
        self.on_leave.reset_mock()

        self.presence_sim.leave()
        self.on_leave.wait_for_call()

        self.assertIsNone(self.presence.present_vehicles.get("gate_in"))

    def test_lpr_change(self):
        vehicle_0 = self.presence_sim.vehicle().lpr("A", "GARIVO1")
        self.presence_sim.enter(vehicle_0)
        self.on_enter.wait_for_call()
        self.assertEqual("GARIVO1", self.presence.present_vehicles["gate_in"].lpr.id)

        vehicle_0.lpr("A", "GARIVO2")
        self.presence_sim.change(vehicle_0)
        self.on_change.wait_for_call()
        self.assertEqual("GARIVO2", self.presence.present_vehicles["gate_in"].lpr.id)

    def test_make_model_change(self):
        vehicle_0 = self.presence_sim.vehicle().lpr("A", "GARIVO1")
        self.presence_sim.enter(vehicle_0)
        self.on_enter.wait_for_call()
        self.assertEqual("GARIVO1", self.presence.present_vehicles["gate_in"].lpr.id)

        vehicle_0.set_make_model(MakeModel(make="TESLA", make_confidence=0.7, model="UNKNOWN", model_confidence=-1.0))
        self.presence_sim.change(vehicle_0)
        self.on_change.wait_for_call()
        self.assertEqual("TESLA", self.presence.present_vehicles["gate_in"].make_model.make)

    def test_normal(self):
        self.presence_sim.enter(self.presence_sim.vehicle().lpr("A", "G ARIVO1"))
        self.on_enter.wait_for_call()
        self.assertEqual("G ARIVO1", self.presence.present_vehicles["gate_in"].lpr.id)

        self.presence_sim.leave()
        self.on_leave.wait_for_call()
        self.assertEqual({}, self.presence.present_vehicles)

    def test_other_calls(self):
        vehicle = self.presence_sim.vehicle().lpr("A", "G ARIVO1")

        self.presence_sim.forward(vehicle)
        self.on_forward.wait_for_call()

        self.presence_sim.backward(vehicle)
        self.on_backward.wait_for_call()

        self.presence_sim.enter(vehicle)
        self.on_enter.wait_for_call()

        vehicle_changed = vehicle.nfc("asdf")
        self.presence_sim.change(vehicle_changed)
        self.on_change.wait_for_call()
        self.on_change.reset_mock()

    def test_missed_enter_before_change(self):
        self.presence_sim.change_before_enter(self.presence_sim.vehicle().lpr("A", "G ARIVO1"))
        self.on_enter.wait_for_call()
        self.assertEqual("G ARIVO1", self.presence.present_vehicles["gate_in"].lpr.id)

        self.presence_sim.leave()
        self.on_leave.wait_for_call()
        self.assertEqual({}, self.presence.present_vehicles)

    def test_enter_direction(self):
        vehicle = self.presence_sim.vehicle().lpr("A", "G ARIVO1")
        self.presence_sim.enter(vehicle)
        self.on_enter.wait_for_call()
        self.assertEqual(EnterDirection.unknown, self.presence.present_vehicles["gate_in"].enter_direction)

        vehicle.set_enter_direction(EnterDirection.forward)
        self.presence_sim.change(vehicle)
        self.on_change.wait_for_call()
        self.assertEqual(EnterDirection.forward, self.presence.present_vehicles["gate_in"].enter_direction)

        self.presence_sim.leave()
        self.on_leave.wait_for_call()

        self.on_enter.reset_mock()
        self.on_change.reset_mock()
        self.on_leave.reset_mock()

        vehicle = self.presence_sim.vehicle().lpr("A", "G ARIVO1").set_enter_direction(EnterDirection.backward)
        self.presence_sim.enter(vehicle)
        self.on_enter.wait_for_call()
        self.assertEqual(EnterDirection.backward, self.presence.present_vehicles["gate_in"].enter_direction)

        self.presence_sim.leave()
        self.on_leave.wait_for_call()
        self.assertEqual({}, self.presence.present_vehicles)

        self.on_enter.reset_mock()
        self.on_change.reset_mock()
        self.on_leave.reset_mock()

        vehicle = self.presence_sim.vehicle().lpr("A", "G ARIVO1")
        self.presence_sim.enter(vehicle)
        self.on_enter.wait_for_call()
        self.assertEqual(EnterDirection.unknown, self.presence.present_vehicles["gate_in"].enter_direction)

        # no change is sent when enter direction changes, so change can also happen on forward / backward / leave
        vehicle.set_enter_direction(EnterDirection.backward)
        self.presence_sim.leave()
        self.on_leave.wait_for_call()
        self.presence_sim.forward(vehicle)
        self.on_forward.wait_for_call()
        self.assertEqual(EnterDirection.backward, self.on_forward.call_args[0][0].enter_direction)

    def test_missing_leave(self):
        vehicle = self.presence_sim.vehicle().lpr("A", "G ARIVO1")
        self.presence_sim.enter(vehicle)
        self.on_enter.wait_for_call()
        self.presence_sim.forward(vehicle)
        self.on_leave.wait_for_call()
        self.assertIsNotNone(self.on_leave.call_args[0][0].leave_time)
        self.on_forward.wait_for_call()

    def test_missing_leave_new_enter(self):
        vehicle = self.presence_sim.vehicle().lpr("A", "G ARIVO1")
        vehicle2 = self.presence_sim.vehicle().lpr("A", "G ARIVO2")
        self.presence_sim.enter(vehicle)
        self.presence_sim.enter_without_dropping_present_vehicle(vehicle2)
        self.on_leave.wait_for_call()
        self.assertEqual(self.on_leave.call_args_list[0].args[0].id, vehicle.vehicle_id)
        self.assertIsNotNone(self.on_leave.call_args_list[0].args[0].leave_time)

    def test_enter_before_forward(self):
        vehicle1 = self.presence_sim.vehicle().lpr("A", "G ARIVO1")
        vehicle2 = self.presence_sim.vehicle().lpr("A", "G ARIVO2")
        self.presence_sim.enter(vehicle1)
        self.on_enter.wait_for_call()
        self.presence_sim.leave()
        self.on_leave.wait_for_call()
        self.on_enter.reset_mock()
        self.presence_sim.enter(vehicle2)
        self.on_enter.wait_for_call()
        self.presence_sim.forward(vehicle1)
        self.on_forward.wait_for_call()
        self.assertIsNotNone(self.presence.present_vehicles.get("gate_in"))
        self.on_leave.reset_mock()
        self.presence_sim.leave()
        self.on_leave.wait_for_call()
        self.on_forward.reset_mock()
        self.presence_sim.forward(vehicle2)
        self.on_forward.wait_for_call()

    def test_qr_binary(self):
        vehicle = self.presence_sim.vehicle().qr("QR1", "aGFsbG8=")
        self.presence_sim.enter(vehicle)
        self.assertEqual(self.presence.present_vehicles["gate_in"].qr.binary, "aGFsbG8=")

    def test_reenter_immediate(self):
        vehicle1 = self.presence_sim.vehicle().lpr("A", "G ARIVO1")
        self.presence_sim.enter(vehicle1)
        self.on_enter.wait_for_call()
        self.presence_sim.leave()
        self.on_leave.wait_for_call()
        self.on_enter.reset_mock()
        self.on_leave.reset_mock()
        self.presence_sim.enter(vehicle1)
        self.on_enter.wait_for_call()
        self.presence_sim.leave()
        self.on_leave.wait_for_call()
        self.on_forward.reset_mock()
        self.presence_sim.forward(vehicle1)
        self.on_forward.wait_for_call()

    def test_reenter_empty_first(self):
        vehicle1 = self.presence_sim.vehicle().lpr("A", "G ARIVO1")
        vehicle2 = self.presence_sim.vehicle()
        self.presence_sim.enter(vehicle1)
        self.on_enter.wait_for_call()
        self.presence_sim.leave()
        self.on_leave.wait_for_call()
        self.on_enter.reset_mock()
        self.on_leave.reset_mock()
        self.presence_sim.enter(vehicle2)
        self.on_enter.wait_for_call()
        self.on_enter.reset_mock()
        self.presence_sim.change_vehicle_and_id(vehicle1)
        self.on_leave.wait_for_call()
        self.on_enter.wait_for_call()
        self.on_leave.reset_mock()
        self.presence_sim.leave()
        self.on_leave.wait_for_call()
        self.on_forward.reset_mock()
        self.presence_sim.forward(vehicle1)
        self.on_forward.wait_for_call()

    def test_leave_of_another_vehicle(self):
        vehicle1 = self.presence_sim.vehicle().lpr("A", "G ARIVO1")
        vehicle2 = self.presence_sim.vehicle().lpr("A", "G ARIVO2")
        self.presence_sim.enter(vehicle1)
        self.on_enter.wait_for_call()
        self.presence_sim.leave_without_present(vehicle2)
        self.on_leave.wait_for_call(minimum_call_count=2)
        self.assertEqual(self.on_leave.call_args_list[0].args[0].id, vehicle1.vehicle_id)
        self.assertIsNotNone(self.on_leave.call_args_list[0].args[0].leave_time)
        self.assertEqual(self.on_leave.call_args_list[1].args[0].id, vehicle2.vehicle_id)
        self.assertIsNotNone(self.on_leave.call_args_list[0].args[0].leave_time)


class PresenceTestUtilsTest(BasePresenceTest):
    def test_vehicle_id_change_is_enforced(self):
        vehicle = self.presence_sim.vehicle().lpr("A", "G ARIVO1")
        self.presence_sim.enter(vehicle)

        with self.assertRaises(AssertionError) as e:
            self.presence_sim.change_vehicle_and_id(vehicle)
        self.assertIn("vehicle id must change", str(e.exception))

        self.on_enter.reset_mock()
        self.presence_sim.change_vehicle_and_id(self.presence_sim.vehicle().lpr("A", "G ARIVO1"))
        self.on_leave.wait_for_call()
        self.on_enter.wait_for_call()


class GateFilterTest(BasePresenceTest):
    def setUp(self) -> None:
        super().setUp()
        self.presence2 = PresenceListener(self.dispatcher, "gate_in")
        self.on_enter2 = MockEvent()
        self.presence2.on_enter.append(self.on_enter2)

    def tearDown(self):
        super().tearDown()

    def test_gate_filter(self):
        self.presence_sim.enter(self.presence_sim.vehicle().lpr("A", "G ARIVO1"))

        self.on_enter.wait_for_call()
        self.assertIn("gate_in", self.presence.present_vehicles.keys())
        self.presence.present_vehicles = {}
        self.on_enter2.wait_for_call()
        self.assertIn("gate_in", self.presence2.present_vehicles.keys())
        self.presence2.present_vehicles = {}

        MockEvent.reset_all_mocks()

        sim_out = PresenceSimulator("gate_out", Direction.OUT, lambda x: self.dispatcher.dispatch("presence", x))
        sim_out.enter(sim_out.vehicle().lpr("A", "G ARIVO2"))
        self.on_enter.wait_for_call()

        self.assertIn("gate_out", self.presence.present_vehicles.keys())
        with self.assertRaises(TimeoutError):
            self.on_enter2.wait_for_call()

        self.assertEqual({}, self.presence2.present_vehicles)


class PresenceSimulatorTest(TestCase):
    message: PresenceBaseMessage | None = None

    def setUp(self) -> None:
        super().setUp()
        self.message = None

    def test_presence_alias_fields_serialization(self):
        sim = PresenceSimulator("gate1", Direction.IN, partial(setattr, self, "message"))
        sim.enter(sim.vehicle().qr("test"))
        sim.forward()
        message = orjson.loads(self.message.json_bytes())
        self.assertIn("leave-time", message)

    def test_enter_and_leave_time(self):
        sim = PresenceSimulator("gate1", Direction.IN, partial(setattr, self, "message"))
        with freezegun.freeze_time("2021-01-01 12:00:00"):
            vehicle = sim.vehicle()
            enter_time = utcnow()
            sim.enter(vehicle)
            self.assertEqual(self.message.enter_time, enter_time)
        with freezegun.freeze_time("2021-01-01 12:00:01"):
            vehicle.lpr("A", "TEST1")
            sim.change(vehicle)
            self.assertEqual(self.message.enter_time, enter_time)
        with freezegun.freeze_time("2021-01-01 12:00:02"):
            leave_time = utcnow()
            sim.leave()
            self.assertEqual(self.message.enter_time, enter_time)
            self.assertEqual(self.message.leave_time, leave_time)
        with freezegun.freeze_time("2021-01-01 12:00:03"):
            sim.forward(vehicle)
            self.assertEqual(self.message.enter_time, enter_time)
            self.assertEqual(self.message.leave_time, leave_time)

        with freezegun.freeze_time("2021-01-01 12:00:03"):
            enter_time = utcnow()
            vehicle2 = sim.vehicle()
            sim.change_before_enter(vehicle2)
            self.assertEqual(self.message.enter_time, enter_time)
        with freezegun.freeze_time("2021-01-01 12:00:04"):
            leave_time = utcnow()
            sim.backward()
            self.assertEqual(self.message.enter_time, enter_time)
            self.assertEqual(self.message.leave_time, leave_time)
        with freezegun.freeze_time("2021-01-01 12:00:05"):
            vehicle3 = sim.vehicle()
            sim.leave_without_present(vehicle3)
            self.assertEqual(self.message.enter_time, utcnow())
            self.assertEqual(self.message.leave_time, utcnow())


class PresenceRPCTest(OpenModuleCoreTestMixin):
    def setUp(self) -> None:
        super().setUp()
        self.presence_sim = PresenceSimulator("gate_in", Direction.IN, lambda x: self.zmq_client.send("presence", x))
        self.core.rpc_client = MockRPCClient(callbacks={("tracking", "get-present"): self.on_reply})
        self.present = False

    def tearDown(self):
        super().tearDown()

    def on_reply(self, request: PresenceRPCRequest, _) -> PresenceRPCResponse:
        """
        Emulates Trackings Presence RPC
        """
        if self.present:
            return PresenceRPCResponse(presents=[
                PresenceBaseData(vehicle_id=1, source=request.gate, present_area_name=request.gate,
                                 last_update=utcnow(), gateway=Gateway(gate=request.gate, direction=Direction.IN),
                                 medium=PresenceMedia(lpr=LPRMedium(id="T EST 1")), all_ids=PresenceAllIds())])
        else:
            return PresenceRPCResponse(presents=[])

    def test_presence_rpc_plate(self):
        self.present = True
        self.presence = PresenceListener(self.core.messages, gate="gate_in")
        self.presence.init_present_vehicles()
        self.assertNotEqual({}, self.presence.present_vehicles)

    def test_presence_rpc_no_plate(self):
        self.present = False
        self.presence = PresenceListener(self.core.messages, gate="gate_in")
        self.presence.init_present_vehicles()
        self.assertEqual({}, self.presence.present_vehicles)

    def test_presence_rpc_timeout(self):
        self.core.rpc_client.callbacks = {}
        self.presence = PresenceListener(self.core.messages, gate="gate_in")
        self.core.rpc_client.default_timeout = 1
        self.presence.init_present_vehicles()

    def test_presence_rpc_multiple_gates(self):
        self.present = True
        settings = SettingsMocker({("common/gates", ""): {"gate_in": Gate(gate="gate_in", type="entry", name="in"),
                                                          "gate_out": Gate(gate="gate_out", type="exit", name="out")}})
        self.presence = PresenceListener(self.core.messages)
        self.presence.init_present_vehicles(settings)
        self.assertCountEqual(["gate_in", "gate_out"], self.presence.present_vehicles.keys())


class MultiCameraTest(BasePresenceTest):
    def setUp(self) -> None:
        super().setUp()
        self.presence_sim2 = PresenceSimulator("gate_in", Direction.IN,
                                               lambda x: self.dispatcher.dispatch("presence", x),
                                               "gate_in-presence2")

    def test_empty_plates_interleaved(self):
        """
        Test enter1, enter2, leave1, forward1, leave2, forward2
        There should only be events from 1
        """
        vehicle1 = self.presence_sim.vehicle()
        vehicle2 = self.presence_sim.vehicle()

        self.presence_sim.enter(vehicle1)
        self.presence_sim2.enter(vehicle2)
        self.presence_sim.leave()
        self.presence_sim.forward(vehicle1)
        self.presence_sim2.leave()
        self.presence_sim2.forward(vehicle2)

        self.assertEqual(1, self.on_enter.call_count)
        self.assertEqual(1, self.on_leave.call_count)
        self.assertEqual(1, self.on_forward.call_count)
        self.assertEqual(vehicle1.vehicle().id, self.on_enter.call_args[0][0].id)
        self.assertEqual(vehicle1.vehicle().id, self.on_leave.call_args[0][0].id)
        self.assertEqual(vehicle1.vehicle().id, self.on_forward.call_args[0][0].id)

    def test_instant_plates_interleaved(self):
        """
        Test enter1, enter2, leave1, forward1, leave2, forward2
        There should only be events from 1
        """
        vehicle1 = self.presence_sim.vehicle().lpr("A", "T EST 1")
        vehicle2 = self.presence_sim.vehicle().lpr("A", "T EST 2")

        self.presence_sim.enter(vehicle1)
        self.presence_sim2.enter(vehicle2)
        self.presence_sim.leave()
        self.presence_sim.forward(vehicle1)
        self.presence_sim2.leave()
        self.presence_sim2.forward(vehicle2)

        self.assertEqual(1, self.on_enter.call_count)
        self.assertEqual(1, self.on_leave.call_count)
        self.assertEqual(1, self.on_forward.call_count)
        self.assertEqual(vehicle1.vehicle().id, self.on_enter.call_args[0][0].id)
        self.assertEqual(vehicle1.vehicle().id, self.on_leave.call_args[0][0].id)
        self.assertEqual(vehicle1.vehicle().id, self.on_forward.call_args[0][0].id)

    def test_interleaved_delayed_plates(self):
        """
        Test enter1 (no plate), enter2 (no plate), change1, change2, leave1, backward1, leave2, backward2
        There should only be events from 1
        """
        vehicle1 = self.presence_sim.vehicle()
        vehicle2 = self.presence_sim.vehicle()

        self.presence_sim.enter(vehicle1)
        self.presence_sim2.enter(vehicle2)
        vehicle1.lpr("A", "T EST 1")
        self.presence_sim.change(vehicle1)
        vehicle2.lpr("A", "T EST 2")
        self.presence_sim2.change(vehicle2)
        self.presence_sim.leave()
        self.presence_sim.backward(vehicle1)
        self.presence_sim2.leave()
        self.presence_sim2.backward(vehicle2)

        self.assertEqual(1, self.on_enter.call_count)
        self.assertEqual(1, self.on_change.call_count)
        self.assertEqual(1, self.on_leave.call_count)
        self.assertEqual(1, self.on_backward.call_count)
        self.assertEqual(vehicle1.vehicle().id, self.on_enter.call_args[0][0].id)
        self.assertEqual(vehicle1.vehicle().id, self.on_change.call_args[0][0].id)
        self.assertEqual(vehicle1.vehicle().id, self.on_leave.call_args[0][0].id)
        self.assertEqual(vehicle1.vehicle().id, self.on_backward.call_args[0][0].id)

    def test_interleaved_second_has_first_plates(self):
        """
        Test enter1 (no plate), enter2 (no plate), change2, change1, leave2, forward2, leave1, forward1
        There should be an enter and a leave from 1 followed by enter+leave+forward from 2
        """
        vehicle1 = self.presence_sim.vehicle()
        vehicle2 = self.presence_sim.vehicle()

        self.presence_sim.enter(vehicle1)
        self.presence_sim2.enter(vehicle2)
        vehicle2.lpr("A", "T EST 2")
        self.presence_sim2.change(vehicle2)
        self.on_leave.wait_for_call(minimum_call_count=1)
        self.assertEqual(1, self.on_leave.call_count)
        self.assertEqual(vehicle1.vehicle().id, self.on_leave.call_args[0][0].id)
        self.on_leave.reset_mock()
        vehicle1.lpr("A", "T EST 1")
        self.presence_sim.change(vehicle1)
        self.presence_sim2.leave()
        self.presence_sim2.forward(vehicle2)
        self.presence_sim.leave()
        self.presence_sim.forward(vehicle1)

        self.assertEqual(2, self.on_enter.call_count)
        self.assertEqual(0, self.on_change.call_count)
        self.assertEqual(1, self.on_leave.call_count)  # one leave was already processed
        self.assertEqual(1, self.on_forward.call_count)
        self.assertEqual(vehicle1.vehicle().id, self.on_enter.call_args_list[0][0][0].id)
        self.assertEqual(vehicle2.vehicle().id, self.on_enter.call_args_list[1][0][0].id)
        self.assertEqual(vehicle2.vehicle().id, self.on_leave.call_args[0][0].id)
        self.assertEqual(vehicle2.vehicle().id, self.on_forward.call_args[0][0].id)

    def test_first_changed_after_second_leave(self):
        """
        Test enter1 (no plate), enter2 (no plate), change2, change2, leave2, forward2, change1, leave1, forward1
        There should be an enter and a leave from 1 followed by enter+change+leave+forward from 2
        """
        vehicle1 = self.presence_sim.vehicle()
        vehicle2 = self.presence_sim.vehicle()

        self.presence_sim.enter(vehicle1)
        self.on_enter.wait_for_call(minimum_call_count=1)
        self.assertEqual(vehicle1.vehicle().id, self.on_enter.call_args[0][0].id)
        self.on_enter.reset_mock()
        self.presence_sim2.enter(vehicle2)
        vehicle2.lpr("A", "T EST 2")
        self.presence_sim2.change(vehicle2)
        self.on_leave.wait_for_call(minimum_call_count=1)
        self.assertEqual(1, self.on_leave.call_count)
        self.assertEqual(vehicle1.vehicle().id, self.on_leave.call_args[0][0].id)
        self.on_leave.reset_mock()
        vehicle2.lpr("A", "T EST 3")
        self.presence_sim2.change(vehicle2)
        self.presence_sim2.leave()
        self.presence_sim2.forward(vehicle2)
        vehicle1.lpr("A", "T EST 1")
        self.presence_sim.change(vehicle1)
        self.presence_sim.leave()
        self.presence_sim.forward(vehicle1)

        self.assertEqual(1, self.on_enter.call_count)
        self.assertEqual(1, self.on_change.call_count)
        self.assertEqual(1, self.on_leave.call_count)  # one leave was already processed
        self.assertEqual(1, self.on_forward.call_count)
        self.assertEqual(vehicle2.vehicle().id, self.on_enter.call_args[0][0].id)
        self.assertEqual(vehicle2.vehicle().id, self.on_change.call_args[0][0].id)
        self.assertEqual(vehicle2.vehicle().id, self.on_leave.call_args[0][0].id)
        self.assertEqual(vehicle2.vehicle().id, self.on_forward.call_args[0][0].id)

    def test_interleaved_delayed_mediums(self):
        """
        Test enter1 (no plate), enter2 (no plate), change1, change2, leave1, backward1, leave2, backward2
        There should only be events from 1
        """
        vehicle1 = self.presence_sim.vehicle()
        vehicle2 = self.presence_sim.vehicle()

        self.presence_sim.enter(vehicle1)
        self.presence_sim2.enter(vehicle2)
        vehicle1.qr("QR1")
        self.presence_sim.change(vehicle1)
        vehicle2.lpr("A", "T EST 2")
        self.presence_sim2.change(vehicle2)
        self.presence_sim.leave()
        self.presence_sim.backward(vehicle1)
        self.presence_sim2.leave()
        self.presence_sim2.backward(vehicle2)

        self.assertEqual(1, self.on_enter.call_count)
        self.assertEqual(1, self.on_change.call_count)
        self.assertEqual(1, self.on_leave.call_count)
        self.assertEqual(1, self.on_backward.call_count)
        self.assertEqual(vehicle1.vehicle().id, self.on_enter.call_args[0][0].id)
        self.assertEqual(vehicle1.vehicle().id, self.on_change.call_args[0][0].id)
        self.assertEqual(vehicle1.vehicle().id, self.on_leave.call_args[0][0].id)
        self.assertEqual(vehicle1.vehicle().id, self.on_backward.call_args[0][0].id)


class MultiCameraDeduplicationTest(BasePresenceTest):
    def setUp(self) -> None:
        super().setUp()
        self.presence_sim2 = PresenceSimulator("gate_in", Direction.IN,
                                               lambda x: self.dispatcher.dispatch("presence", x),
                                               "gate_in-presence2")

    def test_reenter_same_present_area(self):
        """
        Test enter1, leave1, forward1, enter1 (no plate), change1, leave1, forward1
        No event should be dropped
        """
        vehicle1 = self.presence_sim.vehicle().lpr("A", "T EST 1")
        self.presence_sim.enter(vehicle1)
        self.presence_sim.leave()
        self.presence_sim.forward(vehicle1)

        vehicle2 = self.presence_sim.vehicle()
        self.presence_sim.enter(vehicle2)
        vehicle2.lpr("A", "T EST 1")
        self.presence_sim.change(vehicle2)
        self.presence_sim.leave()
        self.presence_sim.forward(vehicle2)

        self.on_forward.wait_for_call(minimum_call_count=2)

        self.assertEqual(2, self.on_enter.call_count)
        self.assertEqual(1, self.on_change.call_count)
        self.assertEqual(2, self.on_leave.call_count)
        self.assertEqual(2, self.on_forward.call_count)

    def test_duplicate_no_plate(self):
        """
        Test enter1, leave1, forward1, enter2 (no plate), leave2, forward2
        There should only be events from 1
        """
        vehicle1 = self.presence_sim.vehicle().lpr("A", "T EST 1")
        self.presence_sim.enter(vehicle1)
        self.presence_sim.leave()
        self.presence_sim.forward(vehicle1)

        vehicle2 = self.presence_sim2.vehicle()
        self.presence_sim2.enter(vehicle2)
        self.presence_sim2.leave()
        self.presence_sim2.forward(vehicle2)

        self.assertEqual(1, self.on_enter.call_count)
        self.assertEqual(1, self.on_leave.call_count)
        self.assertEqual(1, self.on_forward.call_count)

    def test_duplicate_same_plate(self):
        """
        Test enter1, leave1, forward1, enter2, leave2, forward2
        There should only be events from 1
        """
        vehicle1 = self.presence_sim.vehicle().lpr("A", "T ESTÖQ 1")
        self.presence_sim.enter(vehicle1)
        self.presence_sim.leave()
        self.presence_sim.forward(vehicle1)

        vehicle2 = self.presence_sim2.vehicle().lpr("A", "T ESTO01")
        self.presence_sim2.enter(vehicle2)
        self.presence_sim2.leave()
        self.presence_sim2.forward(vehicle2)

        self.assertEqual(1, self.on_enter.call_count)
        self.assertEqual(1, self.on_leave.call_count)
        self.assertEqual(1, self.on_forward.call_count)

    def test_duplicate_different_plate(self):
        """
        Test enter1, leave1, forward1, enter2, leave2, forward2
        No events should be dropped because of different plates
        """
        vehicle1 = self.presence_sim.vehicle().lpr("A", "T EST 1")
        self.presence_sim.enter(vehicle1)
        self.presence_sim.leave()
        self.presence_sim.forward(vehicle1)

        vehicle2 = self.presence_sim2.vehicle().lpr("A", "T EST 2")
        self.presence_sim2.enter(vehicle2)
        self.presence_sim2.leave()
        self.presence_sim2.forward(vehicle2)

        self.on_forward.wait_for_call(minimum_call_count=2)

        self.assertEqual(2, self.on_enter.call_count)
        self.assertEqual(2, self.on_leave.call_count)
        self.assertEqual(2, self.on_forward.call_count)

    def test_duplicate_change_to_different_plate(self):
        """
        Test enter1, leave1, forward1, enter2 (no plate), change2, leave2, forward2
        Enter2 should be dropped the rest should not be dropped because of different plates
        """
        vehicle1 = self.presence_sim.vehicle().lpr("A", "T EST 1")
        self.presence_sim.enter(vehicle1)
        self.presence_sim.leave()
        self.presence_sim.forward(vehicle1)

        vehicle2 = self.presence_sim2.vehicle()
        self.presence_sim2.enter(vehicle2)
        vehicle2.lpr("A", "T EST 2")
        self.presence_sim2.change(vehicle2)
        self.presence_sim2.leave()
        self.presence_sim2.forward(vehicle2)

        self.on_forward.wait_for_call(minimum_call_count=2)

        self.assertEqual(2, self.on_enter.call_count)
        self.assertEqual(0, self.on_change.call_count)
        self.assertEqual(2, self.on_leave.call_count)
        self.assertEqual(2, self.on_forward.call_count)

    def test_duplicate_change_to_same_plate(self):
        """
        Test enter1, leave1, forward1, enter2 (different plate), change2 (same plate), leave2, forward2
        No event should be dropped as we need corresponding events for second enter, even if plate changed to the same
        """
        vehicle1 = self.presence_sim.vehicle().lpr("A", "T EST 1")
        self.presence_sim.enter(vehicle1)
        self.presence_sim.leave()
        self.presence_sim.forward(vehicle1)

        vehicle2 = self.presence_sim2.vehicle().lpr("A", "T EST 2")
        self.presence_sim2.enter(vehicle2)
        vehicle2.lpr("A", "T EST 1")
        self.presence_sim2.change(vehicle2)
        self.presence_sim2.leave()
        self.presence_sim2.forward(vehicle2)

        self.on_forward.wait_for_call(minimum_call_count=2)

        self.assertEqual(2, self.on_enter.call_count)
        self.assertEqual(1, self.on_change.call_count)
        self.assertEqual(2, self.on_leave.call_count)
        self.assertEqual(2, self.on_forward.call_count)

    def test_duplicate_same_plate_with_additional(self):
        """
        Test enter1, leave1, forward1, enter1, leave1, forward1, enter2, leave2, forward2
        Events from 2 should be dropped
        """
        vehicle1 = self.presence_sim.vehicle().lpr("A", "T EST 1")
        self.presence_sim.enter(vehicle1)
        self.presence_sim.leave()
        self.presence_sim.forward(vehicle1)
        vehicle1 = self.presence_sim.vehicle().lpr("A", "T EST 2")
        self.presence_sim.enter(vehicle1)
        self.presence_sim.leave()
        self.presence_sim.forward(vehicle1)

        vehicle2 = self.presence_sim2.vehicle().lpr("A", "T EST 1")
        self.presence_sim2.enter(vehicle2)
        self.presence_sim2.leave()
        self.presence_sim2.forward(vehicle2)

        self.assertEqual(2, self.on_enter.call_count)
        self.assertEqual(2, self.on_leave.call_count)
        self.assertEqual(2, self.on_forward.call_count)

    def test_duplicate_afterwards_with_qr(self):
        """
        Test enter1, leave1, forward1, enter2, leave2, forward2
        Events from 2 should be dropped
        """
        vehicle1 = self.presence_sim.vehicle().lpr("A", "T EST 1")
        self.presence_sim.enter(vehicle1)
        self.presence_sim.leave()
        self.presence_sim.forward(vehicle1)

        vehicle2 = self.presence_sim2.vehicle().qr("QR1")
        self.presence_sim2.enter(vehicle2)
        vehicle2.lpr("A", "T EST 1")
        self.presence_sim2.change(vehicle2)  # this is not possible for Tracking at the moment but should be no problem
        self.presence_sim2.leave()
        self.presence_sim2.forward(vehicle2)

        self.assertEqual(2, self.on_enter.call_count)
        self.assertEqual(2, self.on_leave.call_count)
        self.assertEqual(2, self.on_forward.call_count)

    def test_duplicate_after_timeout(self):
        """
        Test enter1, leave1, forward1, wait, enter2, leave2, forward2
        No events should be dropped as time between is long enough
        """
        with freezegun.freeze_time("2020-01-01 00:00"):
            vehicle1 = self.presence_sim.vehicle().lpr("A", "T EST 1")
            self.presence_sim.enter(vehicle1)
            self.presence_sim.leave()
            self.presence_sim.forward(vehicle1)

            self.on_forward.wait_for_call(minimum_call_count=1)
            self.assertEqual(1, self.on_enter.call_count)
            self.assertEqual(1, self.on_leave.call_count)
            self.assertEqual(1, self.on_forward.call_count)

        self.on_enter.reset_mock()
        self.on_leave.reset_mock()
        self.on_forward.reset_mock()

        with freezegun.freeze_time("2020-01-01 00:01"):
            vehicle2 = self.presence_sim2.vehicle().lpr("A", "T EST 1")
            self.presence_sim2.enter(vehicle2)
            self.presence_sim2.leave()
            self.presence_sim2.forward(vehicle2)

            self.on_forward.wait_for_call(minimum_call_count=1)
            self.assertEqual(1, self.on_enter.call_count)
            self.assertEqual(1, self.on_leave.call_count)
            self.assertEqual(1, self.on_forward.call_count)

    def test_duplicate_timeout_before_leave(self):
        """
        Test enter1, leave1, forward1, enter2, wait, leave2, forward2
        Events of 2 should be dropped as enter2 was within timeout and all events of the vehicle should be dropped
        """
        with freezegun.freeze_time("2020-01-01 00:00"):
            vehicle1 = self.presence_sim.vehicle().lpr("A", "T EST 1")
            self.presence_sim.enter(vehicle1)
            self.presence_sim.leave()
            self.presence_sim.forward(vehicle1)
            vehicle2 = self.presence_sim2.vehicle().lpr("A", "T EST 1")
            self.presence_sim2.enter(vehicle2)

            self.assertEqual(1, self.on_enter.call_count)
            self.assertEqual(1, self.on_leave.call_count)
            self.assertEqual(1, self.on_forward.call_count)

        self.on_enter.reset_mock()
        self.on_leave.reset_mock()
        self.on_forward.reset_mock()

        with freezegun.freeze_time("2020-01-01 00:01"):
            self.presence_sim2.leave()
            self.presence_sim2.forward(vehicle2)

            self.assertEqual(0, self.on_enter.call_count)
            self.assertEqual(0, self.on_leave.call_count)
            self.assertEqual(0, self.on_forward.call_count)

    def test_duplicate_change_after_timeout(self):
        """
        Test enter1, leave1, forward1, enter2, wait, change2, leave2, forward2
        Enter2 should be dropped however the is a change2 after the timeout so change2, leave2, forward2 are not dropped
        """
        with freezegun.freeze_time("2020-01-01 00:00"):
            vehicle1 = self.presence_sim.vehicle().lpr("A", "T EST 1")
            self.presence_sim.enter(vehicle1)
            self.presence_sim.leave()
            self.presence_sim.forward(vehicle1)
            vehicle2 = self.presence_sim2.vehicle().lpr("A", "T EST 1")
            self.presence_sim2.enter(vehicle2)

            self.assertEqual(1, self.on_enter.call_count)
            self.assertEqual(1, self.on_leave.call_count)
            self.assertEqual(1, self.on_forward.call_count)

        self.on_enter.reset_mock()
        self.on_leave.reset_mock()
        self.on_forward.reset_mock()

        with freezegun.freeze_time("2020-01-01 00:01"):
            vehicle2.lpr("A", "T EST 2")
            self.presence_sim2.change(vehicle2)
            self.presence_sim2.leave()
            self.presence_sim2.forward(vehicle2)

            self.on_forward.wait_for_call(minimum_call_count=1)

            self.assertEqual(1, self.on_enter.call_count)
            self.assertEqual(0, self.on_change.call_count)
            self.assertEqual(1, self.on_leave.call_count)
            self.assertEqual(1, self.on_forward.call_count)

    def test_last_vehicle_data_cleanup(self):
        """
        Test if cleanup of last_vehicle_data works
        """
        with freezegun.freeze_time("2020-01-01 00:00"):
            vehicle1 = self.presence_sim.vehicle().lpr("A", "T EST 1")
            self.presence_sim.enter(vehicle1)
            self.presence_sim.leave()
            self.presence_sim.forward(vehicle1)
            self.on_forward.wait_for_call(minimum_call_count=1)

        self.on_enter.reset_mock()
        self.on_leave.reset_mock()
        self.on_forward.reset_mock()

        with freezegun.freeze_time("2020-01-01 00:10:09"):
            vehicle1 = self.presence_sim.vehicle().lpr("A", "T EST 2")
            self.presence_sim.enter(vehicle1)
            self.presence_sim.leave()
            self.presence_sim.forward(vehicle1)
            self.on_forward.wait_for_call(minimum_call_count=1)

        self.on_enter.reset_mock()
        self.on_leave.reset_mock()
        self.on_forward.reset_mock()

        self.assertEqual(2, len(self.presence.last_vehicle_data[self.presence_sim.gateway.gate]))

        with freezegun.freeze_time("2020-01-01 00:10:11"):
            vehicle1 = self.presence_sim.vehicle().lpr("A", "T EST 3")
            self.presence_sim.enter(vehicle1)
            self.presence_sim.leave()
            self.presence_sim.forward(vehicle1)
            self.on_forward.wait_for_call(minimum_call_count=1)

        self.assertEqual(2, len(self.presence.last_vehicle_data[self.presence_sim.gateway.gate]))

    def test_drop_list_cleanup(self):
        """
        Test if cleanup of drop_list works
        """
        with freezegun.freeze_time("2020-01-01 00:00"):
            vehicle1 = self.presence_sim.vehicle().lpr("A", "T EST 1")
            self.presence_sim.enter(vehicle1)
        with freezegun.freeze_time("2020-01-01 00:00:01"):
            vehicle2 = self.presence_sim2.vehicle().lpr("A", "T EST 1")
            self.presence_sim2.enter(vehicle2)
            self.presence_sim.leave()
            self.presence_sim.forward(vehicle1)
            self.on_forward.wait_for_call(minimum_call_count=1)

        self.on_enter.reset_mock()
        self.on_leave.reset_mock()
        self.on_forward.reset_mock()

        with freezegun.freeze_time("2020-01-01 00:59"):
            vehicle1 = self.presence_sim.vehicle().lpr("A", "T EST 2")
            self.presence_sim.enter(vehicle1)
            self.presence_sim.leave()
            self.presence_sim.forward(vehicle1)
            self.on_forward.wait_for_call(minimum_call_count=1)
            # no cleanup of vehicle without leave yet
            self.assertEqual(1, len(self.presence.drop_list))

        self.on_enter.reset_mock()
        self.on_leave.reset_mock()
        self.on_forward.reset_mock()

        with freezegun.freeze_time("2020-01-01 01:01"):
            vehicle1 = self.presence_sim.vehicle().lpr("A", "T EST 2")
            self.presence_sim.enter(vehicle1)
            self.presence_sim.leave()
            self.presence_sim.forward(vehicle1)
            self.on_forward.wait_for_call(minimum_call_count=1)
            # now cleanup of vehicle without leave should be done
            self.assertEqual(0, len(self.presence.drop_list))

    def test_jenbach_case(self):
        vehicle1 = self.presence_sim.vehicle()
        vehicle2_1 = self.presence_sim2.vehicle()
        with freezegun.freeze_time("2020-01-01 07:32:30.54"):
            self.presence_sim2.enter(vehicle2_1)
        with freezegun.freeze_time("2020-01-01 07:32:31.11"):
            self.presence_sim.enter(vehicle1)
        with freezegun.freeze_time("2020-01-01 07:32:31.36"):
            self.presence_sim2.leave()
            self.presence_sim2.forward(vehicle2_1)
        with freezegun.freeze_time("2020-01-01 07:32:32.53"):
            vehicle1.lpr("A", "T EST 1")
            self.presence_sim.change(vehicle1)

        self.assertEqual(len(self.presence.present_vehicles), 1)
        self.assertEqual(self.presence.present_vehicles["gate_in"].lpr.id, "T EST 1")

        vehicle2_2 = self.presence_sim2.vehicle()
        with freezegun.freeze_time("2020-01-01 07:32:34.36"):
            self.presence_sim2.enter(vehicle2_2)
        with freezegun.freeze_time("2020-01-01 07:32:41.08"):
            self.presence_sim.leave()
            self.presence_sim.forward(vehicle1)
        with freezegun.freeze_time("2020-01-01 07:32:41.24"):
            self.presence_sim2.leave()
            self.presence_sim2.forward(vehicle2_2)

        self.assertEqual(self.on_enter.call_count, 2)
        self.assertEqual(self.on_enter.call_args[0][0].lpr.id, "T EST 1")
        self.assertEqual(self.on_change.call_count, 0)
        self.assertEqual(self.on_leave.call_count, 2)
        self.assertEqual(self.on_leave.call_args[0][0].lpr.id, "T EST 1")
        self.assertEqual(self.on_forward.call_count, 2)
        self.assertEqual(self.on_forward.call_args[0][0].lpr.id, "T EST 1")
        self.assertEqual(self.on_backward.call_count, 0)

    def test_ploop_and_cloop_bug(self):
        vehicle1_f = self.presence_sim.vehicle()
        vehicle2_f = self.presence_sim.vehicle()
        vehicle1_b = self.presence_sim2.vehicle()
        vehicle2_b = self.presence_sim2.vehicle()

        with freezegun.freeze_time("2023-07-10T15:40:59.984844000"):
            self.presence_sim.enter(vehicle1_f)
        with freezegun.freeze_time("2023-07-10T15:40:59.985813000"):
            self.presence_sim2.enter(vehicle1_b)
        with freezegun.freeze_time("2023-07-10T15:41:00.209423000"):
            vehicle1_f.lpr("A", "W 94332 X")
            self.presence_sim.change(vehicle1_f)
        with freezegun.freeze_time("2023-07-10T15:41:00.283429000"):
            vehicle1_b.lpr("A", "W 94332 X")
            self.presence_sim2.change(vehicle1_b)
        with freezegun.freeze_time("2023-07-10T15:41:36.285722000"):
            self.presence_sim2.leave()
        with freezegun.freeze_time("2023-07-10T15:41:36.289291000"):
            self.presence_sim.leave()
        with freezegun.freeze_time("2023-07-10T15:41:39.948261000"):
            self.presence_sim.enter(vehicle2_f)
        with freezegun.freeze_time("2023-07-10T15:41:39.954914000"):
            vehicle2_b.lpr("A", "MZC-130")
            self.presence_sim2.enter(vehicle2_b)
        with freezegun.freeze_time("2023-07-10T15:41:40.336434000"):
            vehicle2_f.lpr("A", "MZC-130")
            self.presence_sim.change(vehicle2_f)
        with freezegun.freeze_time("2023-07-10T15:41:41.330551000"):
            self.presence_sim.forward(vehicle1_f)
        with freezegun.freeze_time("2023-07-10T15:41:41.339607000"):
            self.presence_sim2.forward(vehicle1_b)
        with freezegun.freeze_time("2023-07-10T15:41:55.399396000"):
            self.presence_sim.leave()
        with freezegun.freeze_time("2023-07-10T15:41:55.400607000"):
            self.presence_sim2.leave()
        with freezegun.freeze_time("2023-07-10T15:42:00.496283000"):
            self.presence_sim.forward(vehicle2_f)
        with freezegun.freeze_time("2023-07-10T15:42:01.081898000"):
            self.presence_sim2.forward(vehicle2_b)

        self.assertEqual(self.on_forward.call_count, 2)

    def test_ploop_and_cloop_bug2(self):
        vehicle1_f = self.presence_sim.vehicle()
        vehicle2_f = self.presence_sim.vehicle()
        vehicle1_b = self.presence_sim2.vehicle()
        vehicle2_b = self.presence_sim2.vehicle()

        with freezegun.freeze_time("2023-07-10T15:40:59.984844000"):
            self.presence_sim.enter(vehicle1_f)
        with freezegun.freeze_time("2023-07-10T15:40:59.985813000"):
            self.presence_sim2.enter(vehicle1_b)
        with freezegun.freeze_time("2023-07-10T15:41:00.209423000"):
            vehicle1_f.lpr("A", "W 94332 X")
            self.presence_sim.change(vehicle1_f)
        with freezegun.freeze_time("2023-07-10T15:41:00.283429000"):
            vehicle1_b.lpr("A", "W 94332 X")
            self.presence_sim2.change(vehicle1_b)
        with freezegun.freeze_time("2023-07-10T15:41:36.285722000"):
            self.presence_sim2.leave()
        with freezegun.freeze_time("2023-07-10T15:41:36.289291000"):
            self.presence_sim.leave()
        with freezegun.freeze_time("2023-07-10T15:41:39.954914000"):
            vehicle2_b.lpr("A", "MZC-130")
            self.presence_sim2.enter(vehicle2_b)
        with freezegun.freeze_time("2023-07-10T15:41:40.336434000"):
            vehicle2_f.lpr("A", "MZC-130")
            self.presence_sim.enter(vehicle2_f)
        with freezegun.freeze_time("2023-07-10T15:41:41.330551000"):
            self.presence_sim.forward(vehicle1_f)
        with freezegun.freeze_time("2023-07-10T15:41:41.339607000"):
            self.presence_sim2.forward(vehicle1_b)
        with freezegun.freeze_time("2023-07-10T15:41:55.399396000"):
            self.presence_sim.leave()
        with freezegun.freeze_time("2023-07-10T15:41:55.400607000"):
            self.presence_sim2.leave()
        with freezegun.freeze_time("2023-07-10T15:42:00.496283000"):
            self.presence_sim.forward(vehicle2_f)
        with freezegun.freeze_time("2023-07-10T15:42:01.081898000"):
            self.presence_sim2.forward(vehicle2_b)

        self.assertEqual(self.on_forward.call_count, 2)

    def test_bc20_bug(self):
        with freezegun.freeze_time("2023-10-10 11:56:32.165526"):
            v_b_1 = self.presence_sim2.vehicle()
            self.presence_sim2.enter(v_b_1)
        with freezegun.freeze_time("2023-10-10 11:56:32.166841"):
            v_f_1 = self.presence_sim.vehicle().lpr("A", "W 26987 K")
            self.presence_sim.enter(v_f_1)
        with freezegun.freeze_time("2023-10-10 11:56:32.587058"):
            v_b_1.lpr("A", "W 26987 K")
            self.presence_sim2.change(v_b_1)
        with freezegun.freeze_time("2023-10-10 12:01:31.760225"):
            self.presence_sim2.leave()
        with freezegun.freeze_time("2023-10-10 12:01:31.759302"):
            self.presence_sim.leave()
        with freezegun.freeze_time("2023-10-10 12:02:53.827106"):
            self.presence_sim2.backward(v_b_1)
        with freezegun.freeze_time("2023-10-10 12:02:53.829588"):
            self.presence_sim2.enter(v_b_1)
        with freezegun.freeze_time("2023-10-10 12:02:53.829843"):
            self.presence_sim.backward(v_f_1)
        with freezegun.freeze_time("2023-10-10 12:02:53.830568"):
            self.presence_sim.enter(v_f_1)
        with freezegun.freeze_time("2023-10-10 12:02:56.357673"):
            self.presence_sim2.leave()
        with freezegun.freeze_time("2023-10-10 12:02:56.358557"):
            self.presence_sim.leave()
        with freezegun.freeze_time("2023-10-10 12:03:00.307271"):
            self.presence_sim2.backward(v_b_1)
        with freezegun.freeze_time("2023-10-10 12:03:00.309965"):
            self.presence_sim2.enter(v_b_1)
        with freezegun.freeze_time("2023-10-10 12:03:00.307285"):
            self.presence_sim.backward(v_f_1)
        with freezegun.freeze_time("2023-10-10 12:03:00.309882"):
            self.presence_sim.enter(v_f_1)
        with freezegun.freeze_time("2023-10-10 12:03:02.343375"):
            self.presence_sim2.leave()
        with freezegun.freeze_time("2023-10-10 12:03:02.343907"):
            self.presence_sim.leave()
        with freezegun.freeze_time("2023-10-10 12:03:20.900678"):
            self.presence_sim2.backward(v_b_1)
        with freezegun.freeze_time("2023-10-10 12:03:20.899028"):
            self.presence_sim.backward(v_f_1)
        with freezegun.freeze_time("2023-10-10 12:03:20.905495"):
            self.presence_sim2.enter(v_b_1)
        with freezegun.freeze_time("2023-10-10 12:03:20.906998"):
            self.presence_sim.enter(v_f_1)
        with freezegun.freeze_time("2023-10-10 12:03:24.183102"):
            self.presence_sim.leave()
        with freezegun.freeze_time("2023-10-10 12:03:24.195268"):
            self.presence_sim2.leave()
        with freezegun.freeze_time("2023-10-10 12:03:27.228872"):
            self.presence_sim2.backward(v_b_1)
        with freezegun.freeze_time("2023-10-10 12:03:28.709402"):
            self.presence_sim.backward(v_f_1)
        with freezegun.freeze_time("2023-10-10 12:03:28.710072"):
            self.presence_sim.enter(v_f_1)
        with freezegun.freeze_time("2023-10-10 12:03:28.733545"):
            v_b_1b = self.presence_sim2.vehicle()
            self.presence_sim2.enter(v_b_1b)
        with freezegun.freeze_time("2023-10-10 12:03:28.890809"):
            v_b_1b.lpr("A", "W 26987 K")
            self.presence_sim2.change(v_b_1b)
        with freezegun.freeze_time("2023-10-10 12:03:46.839473"):
            self.presence_sim2.leave()
        with freezegun.freeze_time("2023-10-10 12:03:46.839426"):
            self.presence_sim.leave()
        with freezegun.freeze_time("2023-10-10 12:03:51.686501"):
            v_f_2 = self.presence_sim.vehicle().lpr("A", "KR 558 ED")
            self.presence_sim.enter(v_f_2)
        with freezegun.freeze_time("2023-10-10 12:03:51.686754"):
            v_b_2 = self.presence_sim2.vehicle()
            self.presence_sim2.enter(v_b_2)
        with freezegun.freeze_time("2023-10-10 12:03:51.779313"):
            v_b_2.lpr("A", "KR 558 ED")
            self.presence_sim2.change(v_b_2)
        with freezegun.freeze_time("2023-10-10 12:03:51.848884"):
            self.presence_sim.forward(v_f_1)
        with freezegun.freeze_time("2023-10-10 12:03:51.898100"):
            self.presence_sim2.forward(v_b_1b)
        with freezegun.freeze_time("2023-10-10 12:03:55.543389"):
            self.presence_sim2.leave()
        with freezegun.freeze_time("2023-10-10 12:03:55.544156"):
            self.presence_sim.leave()
        with freezegun.freeze_time("2023-10-10 12:04:00.630595"):
            self.presence_sim.forward(v_f_2)
        with freezegun.freeze_time("2023-10-10 12:04:01.567160"):
            self.presence_sim2.forward(v_b_2)

        self.assertEqual(self.on_forward.call_count, 2)
        self.assertEqual(self.on_backward.call_count, 4)

    def test_bc20_bug2(self):
        with freezegun.freeze_time("2023-10-17 08:51:48.063690"):
            v_f_1 = self.presence_sim.vehicle()
            self.presence_sim.enter(v_f_1)
        with freezegun.freeze_time("2023-10-17 08:51:48.065298"):
            v_b_1 = self.presence_sim2.vehicle()
            self.presence_sim2.enter(v_b_1)
        with freezegun.freeze_time("2023-10-17 08:51:48.735085"):
            v_b_1.lpr("A", "W 20721 I")
            self.presence_sim2.change(v_b_1)
        with freezegun.freeze_time("2023-10-17 08:51:50.545432"):
            v_f_1.lpr("A", "W 20721 I")
            self.presence_sim.change(v_f_1)
        with freezegun.freeze_time("2023-10-17 08:51:51.208686"):
            self.presence_sim.leave()
        with freezegun.freeze_time("2023-10-17 08:51:51.215856"):
            self.presence_sim2.leave()
        with freezegun.freeze_time("2023-10-17 08:51:51.737718"):
            self.presence_sim2.backward(v_b_1)
        with freezegun.freeze_time("2023-10-17 08:51:54.816448"):
            v_b_2 = self.presence_sim2.vehicle()
            self.presence_sim2.enter(v_b_2)
        with freezegun.freeze_time("2023-10-17 08:51:54.820955"):
            self.presence_sim.backward(v_f_1)
        with freezegun.freeze_time("2023-10-17 08:51:54.824469"):
            self.presence_sim.enter(v_f_1)
        with freezegun.freeze_time("2023-10-17 08:51:55.119734"):
            v_b_2.lpr("A", "W 20721 I")
            self.presence_sim2.change(v_b_2)
        with freezegun.freeze_time("2023-10-17 08:52:04.550828"):
            self.presence_sim.leave()
        with freezegun.freeze_time("2023-10-17 08:52:04.552134"):
            self.presence_sim2.leave()
        with freezegun.freeze_time("2023-10-17 08:52:09.661201"):
            self.presence_sim.forward(v_f_1)
        with freezegun.freeze_time("2023-10-17 08:52:10.547332"):
            self.presence_sim2.forward(v_b_2)
        self.assertEqual(self.on_forward.call_count, 1)
        self.assertEqual(self.on_backward.call_count, 1)

    def test_no_leave_time_in_fake_leave(self):
        v_f_1 = self.presence_sim.vehicle()
        self.presence_sim.enter(v_f_1)
        v_b_1 = self.presence_sim2.vehicle().lpr("A", "T EST 1")
        self.presence_sim2.enter(v_b_1)
        self.assertIsNotNone(self.on_leave.call_args[0][0].leave_time)


    # def print_line(self, msg):
    #     print(f'        with freezegun.freeze_time("{datetime.fromtimestamp(msg["timestamp"] - 7200)}"):')
    #     sim = "presence_sim2" if msg["present-area-name"] == "ausfahrt-behind" else "presence_sim"
    #     if msg["type"] == "leave":
    #         call = f'self.{sim}.leave()'
    #     else:
    #         call = f'self.{sim}.{msg["type"]}(v{msg["vehicle_id"]})'
    #     print(f'            {call}')
    #
    # def test_from_messages(self):
    #     with open("/tmp/pres.txt") as f:
    #         msgs = [json.loads(l) for l in f]
    #     for topic, msg in msgs:
    #         if 1697539908 < msg["timestamp"] < 1697540100:
    #             with freezegun.freeze_time(datetime.fromtimestamp(msg["timestamp"] - 7200)):
    #                 print(datetime.fromtimestamp(msg["timestamp"]), msg["vehicle_id"], msg["type"],
    #                       msg["present-area-name"], msg.get("medium", {}).get("lpr", {}).get("id"))
    #                 self.dispatcher.dispatch("presence", msg)
    #                 self.print_line(msg)


class PresenceTimesInVehiclesTest(BasePresenceTest):
    def test_legacy_messages(self):
        common_data = {
            "all_ids": {"lpr": [{"alternatives": [{"confidence": 0.8646211518815814, "plate": "GB 785 BF"}],
                                 "confidence": 0.8646211518815814,
                                 "country": {"code": "A", "confidence": 1.0, "state": "GB"}, "id": "GB 785 BF",
                                 "no_countrylogic_id": "GB 785 BF", "track_id": 1700644411261262589,
                                 "type": "lpr"}]}, "enter_direction": "forward",
            "gateway": {"direction": "in", "gate": "einfahrt"}, "last_update": 1700644412.346482,
            "make_model": {"make": "UNKNOWN", "make_confidence": -1.0, "model": "UNKNOWN", "model_confidence": -1.0},
            "medium": {
                "lpr": {"alternatives": [{"confidence": 0.8646211518815814, "plate": "GB 785 BF"}], "changed": False,
                        "confidence": 0.8646211518815814, "country": {"code": "A", "confidence": 1.0, "state": "GB"},
                        "id": "GB 785 BF", "no_countrylogic_id": "GB 785 BF", "track_id": 1700644411261262589,
                        "type": "lpr"}},
            "present-area-name": "einfahrt", "source": "einfahrt", "vehicle_id": 1700644412346463167}
        with freezegun.freeze_time("2023-11-23 00:00:00.00"):
            enter_msg = common_data.copy()
            enter_msg["timestamp"] = time.time()
            enter_msg["type"] = "enter"
            enter_msg["name"] = "enter"
            self.dispatcher.dispatch("presence", enter_msg)
            self.assertEqual(self.presence.present_vehicles["einfahrt"].enter_time,
                             datetime(2023, 11, 22, 9, 13, 32, 346463))
            self.assertEqual(self.on_enter.call_args.args[0].enter_time, datetime(2023, 11, 22, 9, 13, 32, 346463))
        with freezegun.freeze_time("2023-11-23 00:00:01.00"):
            common_data["medium"]["lpr"]["id"] = "GB 786 BF"
            change_msg = common_data.copy()
            change_msg["timestamp"] = time.time()
            change_msg["type"] = "change"
            change_msg["name"] = "change"
            self.dispatcher.dispatch("presence", change_msg)
            self.assertEqual(self.presence.present_vehicles["einfahrt"].enter_time,
                             datetime(2023, 11, 22, 9, 13, 32, 346463))
            self.assertEqual(self.on_change.call_args.args[0].enter_time, datetime(2023, 11, 22, 9, 13, 32, 346463))
        with freezegun.freeze_time("2023-11-23 00:00:02.00"):
            leave_msg = common_data.copy()
            leave_msg["timestamp"] = time.time()
            leave_msg["type"] = "leave"
            leave_msg["name"] = "leave"
            self.dispatcher.dispatch("presence", leave_msg)
            self.assertEqual(self.on_leave.call_args.args[0].enter_time, datetime(2023, 11, 22, 9, 13, 32, 346463))
            self.assertEqual(self.on_leave.call_args.args[0].leave_time, datetime(2023, 11, 23, 0, 0, 2, 0))
        with freezegun.freeze_time("2023-11-23 00:00:03.00"):
            forward_msg = common_data.copy()
            forward_msg["timestamp"] = time.time()
            forward_msg["type"] = "forward"
            forward_msg["name"] = "forward"
            forward_msg["leave-time"] = 1700644412
            self.dispatcher.dispatch("presence", forward_msg)
            self.assertEqual(self.on_forward.call_args.args[0].enter_time, datetime(2023, 11, 22, 9, 13, 32, 346463))
            self.assertEqual(self.on_forward.call_args.args[0].leave_time, datetime(2023, 11, 22, 9, 13, 32, 0))

    def test_new_messages(self):
        common_data = {
            "all_ids": {"lpr": [{"alternatives": [{"confidence": 0.8646211518815814, "plate": "GB 785 BF"}],
                                 "confidence": 0.8646211518815814,
                                 "country": {"code": "A", "confidence": 1.0, "state": "GB"}, "id": "GB 785 BF",
                                 "no_countrylogic_id": "GB 785 BF", "track_id": 1700644411261262589,
                                 "type": "lpr"}]}, "enter_direction": "forward",
            "gateway": {"direction": "in", "gate": "einfahrt"}, "last_update": 1700644412.346482,
            "enter_time": 1700644412.12345,
            "make_model": {"make": "UNKNOWN", "make_confidence": -1.0, "model": "UNKNOWN", "model_confidence": -1.0},
            "medium": {
                "lpr": {"alternatives": [{"confidence": 0.8646211518815814, "plate": "GB 785 BF"}], "changed": False,
                        "confidence": 0.8646211518815814, "country": {"code": "A", "confidence": 1.0, "state": "GB"},
                        "id": "GB 785 BF", "no_countrylogic_id": "GB 785 BF", "track_id": 1700644411261262589,
                        "type": "lpr"}},
            "present-area-name": "einfahrt", "source": "einfahrt", "vehicle_id": 1700644412346463167}
        with freezegun.freeze_time("2023-11-23 00:00:00.00"):
            enter_msg = common_data.copy()
            enter_msg["timestamp"] = time.time()
            enter_msg["type"] = "enter"
            enter_msg["name"] = "enter"
            self.dispatcher.dispatch("presence", enter_msg)
            self.assertEqual(self.presence.present_vehicles["einfahrt"].enter_time,
                             datetime(2023, 11, 22, 9, 13, 32, 123450))
            self.assertEqual(self.on_enter.call_args.args[0].enter_time, datetime(2023, 11, 22, 9, 13, 32, 123450))
        with freezegun.freeze_time("2023-11-23 00:00:01.00"):
            common_data["medium"]["lpr"]["id"] = "GB 786 BF"
            change_msg = common_data.copy()
            change_msg["timestamp"] = time.time()
            change_msg["type"] = "change"
            change_msg["name"] = "change"
            self.dispatcher.dispatch("presence", change_msg)
            self.assertEqual(self.presence.present_vehicles["einfahrt"].enter_time,
                             datetime(2023, 11, 22, 9, 13, 32, 123450))
            self.assertEqual(self.on_enter.call_args.args[0].enter_time, datetime(2023, 11, 22, 9, 13, 32, 123450))
        with freezegun.freeze_time("2023-11-23 00:00:02.00"):
            leave_msg = common_data.copy()
            leave_msg["timestamp"] = time.time()
            leave_msg["type"] = "leave"
            leave_msg["name"] = "leave"
            leave_msg["leave-time"] = 1700644412
            self.dispatcher.dispatch("presence", leave_msg)
            self.assertEqual(self.on_leave.call_args.args[0].enter_time, datetime(2023, 11, 22, 9, 13, 32, 123450))
            self.assertEqual(self.on_leave.call_args.args[0].leave_time, datetime(2023, 11, 22, 9, 13, 32, 0))
        with freezegun.freeze_time("2023-11-23 00:00:03.00"):
            forward_msg = common_data.copy()
            forward_msg["timestamp"] = time.time()
            forward_msg["type"] = "forward"
            forward_msg["name"] = "forward"
            forward_msg["leave-time"] = 1700644412
            self.dispatcher.dispatch("presence", forward_msg)
            self.assertEqual(self.on_forward.call_args.args[0].enter_time, datetime(2023, 11, 22, 9, 13, 32, 123450))
            self.assertEqual(self.on_forward.call_args.args[0].leave_time, datetime(2023, 11, 22, 9, 13, 32, 0))


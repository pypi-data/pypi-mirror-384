import logging
from datetime import datetime, timedelta

from settings_models.settings.common import GateType

from openmodule import sentry
from openmodule.core import core
from openmodule.dispatcher import EventListener, MessageDispatcher
from openmodule.models.base import Gateway
from openmodule.models.presence import PresenceBaseMessage, PresenceBackwardMessage, PresenceForwardMessage, \
    PresenceChangeMessage, PresenceLeaveMessage, PresenceEnterMessage, PresenceRPCRequest, PresenceRPCResponse
from openmodule.models.vehicle import Vehicle
from openmodule.utils.charset import CharsetConverter, legacy_lpr_charset
from openmodule.utils.misc_functions import utcnow
from openmodule.utils.settings import SettingsProvider


def vehicle_from_presence_message(message: PresenceBaseMessage):
    return Vehicle(
        id=message.vehicle_id,
        lpr=message.medium.lpr,
        qr=message.medium.qr,
        nfc=message.medium.nfc,
        pin=message.medium.pin,
        make_model=message.make_model,
        all_ids=message.all_ids,
        enter_direction=message.enter_direction,
        enter_time=message.enter_time,  # presence message correctly sets fallback
        leave_time=getattr(message, "leave_time", None)
    )


class VehicleDeduplicationData:
    lp_converter = CharsetConverter(legacy_lpr_charset)

    def __init__(self, vehicle: Vehicle, present_area_name: str, timeout: datetime):
        self.plate = VehicleDeduplicationData.lp_converter.clean(vehicle.lpr.id or "")
        self.present_area_name = present_area_name
        self.timeout = timeout
        self.drop_list: set[int] = set()  # vehicle ids to drop

    def update_drop(self, vehicle: Vehicle, present_area_name: str, message_type: str):
        if present_area_name == self.present_area_name:  # never on drop_list if same present area
            return

        plate_matches = vehicle.lpr and self.plate == self.lp_converter.clean(vehicle.lpr.id)
        if message_type == "change" and vehicle.has_media() and not plate_matches:
            # only on change: if vehicle has media but no matching plate, remove from drop list, if exists
            # we don't need to worry that we drop already processed vehicles as presence listener ensures this
            self.drop_list.discard(vehicle.id)
        elif utcnow() > self.timeout:  # don't drop if after timeout
            if message_type == "change":  # on change after timeout, undrop vehicle if exists
                self.drop_list.discard(vehicle.id)
        elif not vehicle.has_media() or (vehicle.lpr and self.plate == self.lp_converter.clean(vehicle.lpr.id)):
            # if none of the above cases and no medium or matching plate, add to drop list
            self.drop_list.add(vehicle.id)

    def should_drop(self, vehicle: Vehicle):
        return vehicle.id in self.drop_list

    def should_cleanup(self):
        return utcnow() > self.timeout + timedelta(minutes=10)  # we have to keep it for longer


class PresenceListener:
    class DropEntry:
        def __init__(self, drop_always: bool, timeout: datetime):
            self.drop_always = drop_always
            self.timeout = timeout

    on_forward: EventListener[tuple[Vehicle, Gateway]]
    on_backward: EventListener[tuple[Vehicle, Gateway]]
    on_enter: EventListener[tuple[Vehicle, Gateway]]
    on_leave: EventListener[tuple[Vehicle, Gateway]]
    on_change: EventListener[tuple[Vehicle, Gateway]]

    present_vehicles: dict[str, Vehicle]  # present vehicle per gate
    # vehicle ids to drop with (bool if always drop or only if no medium, cleanup timestamp)
    # can be shared over all gates (if there are multiple gates) as vehicle id is unique
    drop_list: dict[int, DropEntry]
    never_drop_list: dict[int, Vehicle] = dict()  # vehicle ids and vehicle of not dropped vehicles with medium or leave
    area_name_of_present: dict[str, str]  # present area name of present vehicle per gate
    # Data for deduplication of non-overlapping vehicles (left in first present area before entering in second)
    # data per gate: List because there can be a new one before we are allowed to remove the old one
    last_vehicle_data: dict[str, list[VehicleDeduplicationData]]

    @property
    def present_vehicle(self) -> Vehicle | None:
        assert self.gate is not None, (
            "`.present_vehicle` may only be used when listening for a specific gate, this presence listener"
            "listens to all gates, please access the present vehicle per gate via `.present_vehicles[gate]`"
        )
        return self.present_vehicles.get(self.gate)

    def __init__(self, dispatcher: MessageDispatcher, gate: str | None = None,
                 deduplication_timeout: timedelta = timedelta(seconds=10)):
        assert not dispatcher.is_multi_threaded, (
            "you cannot use a multithreaded message dispatcher for the presence listener. It is highly reliant "
            "on receiving messages in the correct order!"
        )
        self.log = logging.getLogger(self.__class__.__name__ + (" " + gate if gate else ""))
        self.on_forward = EventListener(log=self.log)
        self.on_backward = EventListener(log=self.log)
        self.on_enter = EventListener(log=self.log)
        self.on_change = EventListener(log=self.log)
        self.on_leave = EventListener(log=self.log)
        self.present_vehicles = dict()
        self.drop_list = dict()
        self.never_drop_list = dict()
        self.area_name_of_present = dict()
        self.last_vehicle_data = dict()
        self.deduplication_timeout = deduplication_timeout
        self.gate = gate

        dispatcher.register_handler("presence", PresenceBackwardMessage, self._on_backward)
        dispatcher.register_handler("presence", PresenceForwardMessage, self._on_forward)
        dispatcher.register_handler("presence", PresenceChangeMessage, self._on_change)
        dispatcher.register_handler("presence", PresenceLeaveMessage, self._on_leave)
        dispatcher.register_handler("presence", PresenceEnterMessage, self._on_enter)

    @sentry.trace
    def init_present_vehicles(self, settings_provider: SettingsProvider | None = None):
        if self.gate is None:
            gates = []
            try:
                settings_provider = settings_provider or SettingsProvider(rpc_timeout=1.0)
                gates = settings_provider.get("common/gates")
                gates = [gate_id for gate_id, gate in gates.items() if gate.type != GateType.door]
            except TimeoutError:
                self.log.error("Gate is None and could not get gates (timeout)")
            except Exception:
                self.log.exception("Gate is None and could not get gates")
        else:
            gates = [self.gate]

        reqs = {}
        for gate in gates:
            reqs[gate] = core().rpc_client.rpc_non_blocking("tracking", "get-present", PresenceRPCRequest(gate=gate))
        for gate, request in reqs.items():
            try:
                result = request.result(PresenceRPCResponse)
                if result.presents:
                    self._on_enter(result.presents[0])
            except TimeoutError:
                self.log.error("get-present RPC timeout", extra={"gate": gate})
            except Exception:
                self.log.exception("get-present RPC error", extra={"gate": gate})

    def _gate_matches(self, message: PresenceBaseMessage):
        return (self.gate is None) or (message.gateway.gate == self.gate)

    def _drop_check(self, message: PresenceBaseMessage, vehicle: Vehicle):
        gate = message.gateway.gate
        present_vehicle = self.present_vehicles.get(gate)
        self.last_vehicle_data[gate] = [x for x in self.last_vehicle_data.get(gate, []) if not x.should_cleanup()]
        for x in self.last_vehicle_data[gate]:
            x.update_drop(vehicle, message.present_area_name, message.type)

        # never drop a forward or backward of a vehicle that generated a leave or generated anything with medium
        if vehicle.id in self.never_drop_list:
            return False
        # only drop when in drop list either has no medium or dropped because of vehicle with media
        # (no present means old present was completely processed)
        # also no present_area_name check as vehicle cannot be on drop list if its from the same present area
        elif vehicle.id in self.drop_list and (self.drop_list[vehicle.id].drop_always or not vehicle.has_media()):
            return True
        elif present_vehicle:
            # always allow messages of same vehicle id as present vehicle
            if present_vehicle.id == vehicle.id:
                return False
            # same present area -> no drop, use old behavior
            # (simulate leave for enter and change messages and leave with different vehicle id)
            # not done for forward and backward as there might be a new vehicle from same area present already
            elif self.area_name_of_present.get(gate, "") == message.present_area_name \
                    and message.type in ["enter", "change", "leave"]:
                return False
            # new vehicle is better, simulate leave for old vehicle and remove new vehicle from drop list and add old
            elif not present_vehicle.has_media() and vehicle.has_media():
                self.log.warning("Got better vehicle from another present area. A leave will be faked for the old "
                                 "vehicle to get a consistent setup for the new vehicle.",
                                 extra={"present_vehicle": str(present_vehicle),
                                        "new_vehicle": str(vehicle)})
                # this is different from _execute_leave as we want this vehicle to be on the drop list
                if present_vehicle.leave_time is None:
                    present_vehicle.leave_time = utcnow()
                self.drop_list.pop(vehicle.id, None)  # discard because vehicle might be in drop list
                self.drop_list[present_vehicle.id] = self.DropEntry(True,  # has media
                                                                    utcnow() + timedelta(hours=1))
                self.present_vehicles.pop(gate, None)
                self.on_leave(present_vehicle, message.gateway)
                return False
            # different present area and new vehicle is not better -> drop
            else:
                self.drop_list[vehicle.id] = self.DropEntry(present_vehicle.has_media(),
                                                            utcnow() + timedelta(hours=1))
                return True
        # here we handle case that same vehicle is first seen by camera 1 and after leave seen by camera 2
        elif any([x.should_drop(vehicle) for x in self.last_vehicle_data.get(gate, [])]):
            return True
        else:
            return False

    def _cleanup_drop_list(self):
        # this assumes vehicle id is UTC timestamp in nanoseconds (which is the case unless someone changes Tracking)
        self.drop_list = {k: v for k, v in self.drop_list.items() if utcnow() < v.timeout}
        self.never_drop_list = {k: v for k, v in self.never_drop_list.items()
                                if utcnow() < v.enter_time + timedelta(hours=1)}

    def _fake_leave_if_missing(self, message: PresenceBaseMessage):
        present_vehicle = self.present_vehicles.get(message.gateway.gate)
        if present_vehicle and present_vehicle.id == message.vehicle_id:
            self.log.error(f"Got {message.type} without a leave. We generate a leave ourself.")
            self._on_leave(PresenceLeaveMessage.model_validate(message.model_dump()))

    def _execute_leave(self, vehicle: Vehicle, gateway: Gateway):
        if vehicle.leave_time is None:
            vehicle.leave_time = utcnow()
        self.present_vehicles.pop(gateway.gate, None)
        self.area_name_of_present.pop(gateway.gate, None)
        self.never_drop_list[vehicle.id] = vehicle
        self.on_leave(vehicle, gateway)

    @sentry.trace
    def _on_backward(self, message: PresenceBackwardMessage):
        """
        This handler forwards presence backward  messages to the registered calls in the presence listener
        """

        if not self._gate_matches(message):
            return
        vehicle = vehicle_from_presence_message(message)
        drop_message = self._drop_check(message, vehicle)
        self.drop_list.pop(vehicle.id, None)
        if drop_message:
            return

        self._fake_leave_if_missing(message)

        self.log.debug("presence backward: %s", vehicle)
        self.on_backward(vehicle, message.gateway)
        self.never_drop_list.pop(vehicle.id, None)

    @sentry.trace
    def _on_forward(self, message: PresenceForwardMessage):
        """
        This handler forwards presence forward messages to the registered calls in the presence listener
        """
        if not self._gate_matches(message):
            return
        vehicle = vehicle_from_presence_message(message)
        drop_message = self._drop_check(message, vehicle)
        self.drop_list.pop(vehicle.id, None)
        if drop_message:
            return

        self._fake_leave_if_missing(message)

        self.log.debug("presence forward: %s", vehicle)
        self.on_forward(vehicle, message.gateway)
        self.never_drop_list.pop(vehicle.id, None)

    @sentry.trace
    def _on_leave(self, message: PresenceLeaveMessage):
        """
        This handler forwards presence leave messages to the registered calls in the presence listener
        and clears the present vehicle
        """

        if not self._gate_matches(message):
            return
        leaving_vehicle = vehicle_from_presence_message(message)
        if self._drop_check(message, leaving_vehicle):
            return

        self.log.debug("presence leave: %s", leaving_vehicle)
        present_vehicle = self.present_vehicles.get(message.gateway.gate)
        if present_vehicle:
            if present_vehicle.id != leaving_vehicle.id:
                self.log.error("A vehicle left with a different vehicle id than the present one. Tracking is "
                               "inconsistent. We are fake-leaving the currently present vehicle, to ensure consistent "
                               "states.", extra={"present_vehicle": str(present_vehicle),
                                                 "leaving_vehicle": str(leaving_vehicle)})
                self._execute_leave(present_vehicle, message.gateway)
            self._execute_leave(leaving_vehicle, message.gateway)
            self._cleanup_drop_list()

            if leaving_vehicle.lpr:
                self.last_vehicle_data[message.gateway.gate].append(
                    VehicleDeduplicationData(leaving_vehicle, message.present_area_name,
                                             utcnow() + self.deduplication_timeout))
        else:
            self.log.error("A vehicle left while non was previously present. Tracking is inconsistent. "
                           "The leave will be ignored, to ensure consistent states.",
                           extra={"leaving_vehicle": str(leaving_vehicle)})

    @sentry.trace
    def _on_enter(self, message: PresenceEnterMessage):
        """
        This handler forwards presence enter messages to the registered calls in the presence listener
        and sets the present vehicle
        """

        if not self._gate_matches(message):
            return
        new_vehicle = vehicle_from_presence_message(message)
        if self._drop_check(message, new_vehicle):
            return
        if new_vehicle.has_media():
            self.never_drop_list[new_vehicle.id] = new_vehicle

        self.log.debug("presence enter: %s", new_vehicle)
        present_vehicle = self.present_vehicles.get(message.gateway.gate)
        if present_vehicle:
            self.log.error("A new vehicle entered while one was still present. Tracking is inconsistent. "
                           "A leave will be faked, to ensure consistent states.",
                           extra={"present_vehicle": str(present_vehicle),
                                  "new_vehicle": str(new_vehicle)})
            self._execute_leave(present_vehicle, message.gateway)

        self.present_vehicles[message.gateway.gate] = new_vehicle
        self.area_name_of_present[message.gateway.gate] = message.present_area_name
        self.on_enter(new_vehicle, message.gateway)

    @sentry.trace
    def _on_change(self, message: PresenceChangeMessage):
        """
        This handler forwards presence change messages to the registered calls in the presence listener
        and changes the present vehicle
        """

        if not self._gate_matches(message):
            return
        vehicle = vehicle_from_presence_message(message)

        present_before_drop_check = message.gateway.gate in self.present_vehicles
        if self._drop_check(message, vehicle):
            return

        if vehicle.has_media():
            self.never_drop_list[vehicle.id] = vehicle
        change_with_vehicle_present = message.gateway.gate in self.present_vehicles
        if change_with_vehicle_present and self.present_vehicles[message.gateway.gate].id != vehicle.id:
            self.log.debug("vehicle_id changed in presence change: %s. "
                           "Faking leave and triggering presence enter!", vehicle)
            self._execute_leave(self.present_vehicles[message.gateway.gate], message.gateway)
            change_with_vehicle_present = False

        self.present_vehicles[message.gateway.gate] = vehicle
        self.area_name_of_present[message.gateway.gate] = message.present_area_name
        if change_with_vehicle_present:
            self.log.debug("presence change: %s", vehicle)
            self.on_change(vehicle, message.gateway)
        else:
            if present_before_drop_check:  # only debug log because this is typical behavior in multicamera setups
                self.log.debug("presence enter triggered by change: %s", vehicle)
            else:
                self.log.warning("presence enter triggered by change: %s", vehicle)
            self.on_enter(vehicle, message.gateway)

from enum import StrEnum

from openmodule.models.base import ZMQMessage, OpenModuleModel


class SignalType(StrEnum):
    permanently_closed = "permanently_closed"
    shortterm_full = "shortterm_full"
    open = "open"
    present_raw = "present_raw"
    present_decision = "present_decision"
    traffic_light_green = "traffic_light_green"
    traffic_light_red = "traffic_light_red"
    area_full = "area_full"
    parkinglot_full = "parkinglot_full"
    custom = "custom"


class SignalMessage(ZMQMessage):
    signal: str
    type: SignalType | str  # union so we can add new types without updating all services using signals
    gate: str | None = None
    parking_area_id: str | None = None
    value: bool
    additional_data: dict | None = None


class GetSignalValueRequest(OpenModuleModel):
    signal: str


class GetSignalValueResponse(OpenModuleModel):
    value: bool
    additional_data: dict | None = None


class TriggerSignalsRequest(OpenModuleModel):
    signals: list[str]  # list of signals which current value should be sent


class TriggerSignalsResponse(OpenModuleModel):
    success: bool

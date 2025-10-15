import datetime

from pydantic import ConfigDict, Field, model_validator

from openmodule.models.base import ZMQMessage, OpenModuleModel, Gateway, Datetime
from openmodule.models.vehicle import Medium, LPRMedium, MakeModel, PresenceAllIds, EnterDirection, QRMedium


class PresenceMedia(OpenModuleModel):
    lpr: LPRMedium | None = None
    qr: QRMedium | None = None
    nfc: Medium | None = None
    pin: Medium | None = None


class PresenceBaseData(OpenModuleModel):
    vehicle_id: int
    source: str
    present_area_name: str = Field(
        validation_alias="present-area-name",
        serialization_alias="present-area-name",
    )
    last_update: Datetime
    gateway: Gateway
    medium: PresenceMedia
    make_model: MakeModel | None = None
    all_ids: PresenceAllIds
    enter_direction: EnterDirection = EnterDirection.unknown
    enter_time: Datetime | None = None

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

    def model_post_init(self, *_) -> None:
        if self.enter_time is None:
            self.enter_time = datetime.datetime.fromtimestamp(self.vehicle_id / 1e9, datetime.timezone.utc)


class PresenceBaseMessage(PresenceBaseData, ZMQMessage):
    pass


class PresenceBackwardMessage(PresenceBaseMessage):
    type: str = "backward"
    unsure: bool = False
    leave_time: Datetime = Field(
        validation_alias="leave-time",
        serialization_alias="leave-time",
    )
    bidirectional_inverse: bool = False


class PresenceForwardMessage(PresenceBaseMessage):
    type: str = "forward"
    unsure: bool = False
    leave_time: Datetime = Field(
        validation_alias="leave-time",
        serialization_alias="leave-time",
    )
    bidirectional_inverse: bool = False


class PresenceLeaveMessage(PresenceBaseMessage):
    type: str = "leave"
    num_presents: int = Field(
        default=0,
        validation_alias="num-presents",
        serialization_alias="num-presents",
    )
    leave_time: Datetime = Field(
        validation_alias="leave-time",
        serialization_alias="leave-time",
    )

    @model_validator(mode="before")
    @classmethod
    def set_leave_time_default(cls, values_dict: dict) -> dict:
        if values_dict.get("leave_time") is None:
            values_dict["leave_time"] = values_dict["timestamp"]  # timestamp from message timestamp
        return values_dict


class PresenceEnterMessage(PresenceBaseMessage):
    type: str = "enter"


class PresenceChangeMessage(PresenceBaseMessage):
    type: str = "change"
    change_vehicle_id: bool | None = None


class PresenceRPCRequest(OpenModuleModel):
    gate: str


class PresenceRPCResponse(OpenModuleModel):
    presents: list[PresenceBaseData]

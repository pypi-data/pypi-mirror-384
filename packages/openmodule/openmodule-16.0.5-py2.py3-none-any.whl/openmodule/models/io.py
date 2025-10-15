from openmodule.models.base import ZMQMessage, Gateway, OpenModuleModel, Datetime


class IoMessage(ZMQMessage):
    gateway: Gateway
    type: str
    pin: str
    value: int
    inverted: bool = False
    physical: int | None = None
    edge: int
    pin_number: int | None = None
    pin_label: str | None = None
    meta: dict = {}


class IoState(OpenModuleModel):
    gateway: Gateway
    type: str
    pin: str
    value: int
    inverted: bool
    physical: int
    last_timestamp: Datetime

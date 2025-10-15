from enum import StrEnum

from pydantic import field_validator

from openmodule.models.base import ZMQMessage


class AlertStatus(StrEnum):
    ok = "ok"
    error = "error"
    offline = "offline"


class AlertHandleType(StrEnum):
    state = "state"
    state_change = "state_change"
    count = "count"


class AlertMessage(ZMQMessage):
    type: str = "alert"
    status: AlertStatus
    alert_meta: dict
    package: str
    alert_type: str
    source: str | None = None
    handle_type: AlertHandleType
    value: float | None = None

    @field_validator("value")
    @classmethod
    def require_value_for_state_type(cls, v, values):
        if values.data["handle_type"] == AlertHandleType.state:
            assert v is not None, "value must not be None for alerts with handle_type='state'"
        return v

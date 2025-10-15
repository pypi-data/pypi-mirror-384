from typing import Any

from openmodule.models.base import OpenModuleModel, ZMQMessage


class SettingsGetResponseValue(OpenModuleModel):
    value: Any | None = None
    success: bool
    error: str | None = None


class SettingsGetRequest(OpenModuleModel):
    key: str
    scope: str = ""


SettingsGetResponse = SettingsGetResponseValue


class SettingsGetManyRequest(OpenModuleModel):
    key: list[str]
    scope: str = ""


class SettingsGetManyResponse(OpenModuleModel):
    settings: dict[str, SettingsGetResponseValue]


class SettingsChangedMessage(ZMQMessage):
    type: str = "changed"
    changed_keys: list[str]  # is <key>/<scope>

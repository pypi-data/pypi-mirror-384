import base64
import binascii
import re
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from json.encoder import ESCAPE_ASCII
from typing import Annotated

import orjson
from pydantic_core import PydanticUndefined
import zmq
from dateutil.tz import UTC
from pydantic import AfterValidator, ConfigDict, Field, BaseModel, RootModel

from openmodule import sentry
from openmodule.config import run_checks, settings
from settings_models.settings.common import CostEntryData as SettingsModelsCostEntryData

from openmodule.utils.misc_functions import utcnow


def timezone_validator(dt: datetime) -> datetime:
    if dt and dt.tzinfo:
        return dt.astimezone(UTC).replace(tzinfo=None)
    else:
        return dt


Datetime = Annotated[datetime, AfterValidator(timezone_validator)]

def base64_validator(data: str | bytes) -> str | bytes:
    try:
        base64.b64decode(data)
    except (binascii.Error, TypeError, ValueError):
        raise ValueError("must be a base64 string")
    return data


Base64Payload = Annotated[str | bytes, AfterValidator(base64_validator)]


if run_checks():
    class CheckingModel(type):
        def __new__(mcs, name, bases, dct, **kwargs):
            cls: BaseModel | RootModel = super().__new__(mcs, name, bases, dct, **kwargs)  # type: ignore
 
            for field_name, field in cls.model_fields.items():
                if field.annotation == datetime:
                    assert any(isinstance(metadata, AfterValidator) and metadata.func.__name__ == "timezone_validator"
                               for metadata in field.metadata), (
                        "datetime fields must use the Datetime annotation to ensure all datetime values "
                        "are always naive. Otherwise runtime errors may occur depending on the isoformat used.\n"
                        f"In class {name}, please change to:\n"
                        f"  {field_name}: Datetime ..."
                    )
                    if field.default != PydanticUndefined or field.default_factory:
                        assert field.validate_default or cls.model_config.get("validate_default") is True, (
                            "datetime fields must use the Datetime annotation to ensure all default values "
                            "are validated. Otherwise runtime errors may occur depending on the isoformat used.\n"
                            f"In class {name}, please change to:\n"
                            f"  {field_name}: Datetime ..."
                        )

            return cls


    class CheckingOpenModuleModel(CheckingModel, type(BaseModel), type):
        pass


    class CheckingOpenModuleRootModel(CheckingModel, type(RootModel), type):
        pass


    base_meta_kwargs = {"metaclass": CheckingOpenModuleModel}
    root_meta_kwargs = {"metaclass": CheckingOpenModuleRootModel}
else:  # pragma: no cover
    base_meta_kwargs = {}
    root_meta_kwargs = {}


ESCAPE_ASCII = re.compile(r'([^ -~])')


def replace(match):
    s = match.group(0)
    n = ord(s)
    if n < 0x10000:
        return '\\u%04x' % (n,)
    else:
        # surrogate pair
        n -= 0x10000
        s1 = 0xd800 | ((n >> 10) & 0x3ff)
        s2 = 0xdc00 | (n & 0x3ff)
        return '\\u%04x\\u%04x' % (s1, s2)


def _unicode_escape(data):
    return ESCAPE_ASCII.sub(replace, data)


def default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    if settings.TESTING:
        from freezegun.api import FakeDatetime
        if isinstance(obj, FakeDatetime):
            return obj.isoformat()
    raise TypeError


class _OpenModuleModel(BaseModel):
    model_config = ConfigDict(validate_assignment=True, validate_default=True)

    def json(self, **_):
        assert False, "please use json_bytes"

    def json_bytes(self, **kwargs):
        data = self.model_dump(**kwargs)
        return _unicode_escape(orjson.dumps(data, default=default).decode()).encode("ascii")

    def model_dump(self, **kwargs):
        kwargs.setdefault("by_alias", True)
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)

    def model_dump_json(self, **_) -> str:
        assert False, "please use json_bytes"


class OpenModuleModel(_OpenModuleModel, **base_meta_kwargs):
    pass


class OpenModuleRootModel(RootModel, _OpenModuleModel, **root_meta_kwargs):
    pass


class EmptyModel(OpenModuleModel):
    pass


_EPOCH_UTC = datetime(1970, 1, 1, tzinfo=UTC)
_EPOCH_NAIVE = datetime(1970, 1, 1)


def datetime_to_timestamp(dt: datetime):
    """
    you SHOULD use this function, as it always outputs the UTC unix timestamp, regardless
    of the system's timezone. This is not an issue in production as all systems run UTC,
    but while developing it creates annoying bugs
    """
    if dt.tzinfo is None:
        return (dt - _EPOCH_NAIVE).total_seconds()
    else:
        return (dt - _EPOCH_UTC).total_seconds()


class ZMQMessage(OpenModuleModel):
    timestamp: Datetime = Field(default_factory=lambda: utcnow())

    name: str = Field(default_factory=lambda: settings.NAME)
    type: str
    baggage: str | None = None
    sentry_trace: str | None = Field(
        default=None,
        validation_alias="sentry-trace",
        serialization_alias="sentry-trace",
    )

    def publish_on_topic(self, pub_socket: zmq.Socket, topic: str):
        assert isinstance(topic, str), "topic must be a string"
        self.baggage = sentry.get_baggage()
        self.sentry_trace = sentry.get_traceparent()
        pub_socket.send_multipart((topic.encode("utf8"), self.json_bytes()))

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        data["timestamp"] = datetime_to_timestamp(data["timestamp"])
        return data


class Direction(StrEnum):
    UNKNOWN = ""
    IN = "in"
    OUT = "out"


class Gateway(OpenModuleModel):
    gate: str = ""
    direction: Direction = Direction.UNKNOWN

    def __str__(self):
        return f"{self.gate}/{self.direction}"


# to be not breaking
CostEntryData = SettingsModelsCostEntryData

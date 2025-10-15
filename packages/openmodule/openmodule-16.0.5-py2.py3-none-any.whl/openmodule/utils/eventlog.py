import logging
from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import field_validator, model_validator

from openmodule import sentry
from openmodule.core import core
from openmodule.models.base import OpenModuleModel, ZMQMessage, Datetime
from openmodule.utils.misc_functions import utcnow

log = logging.getLogger("Eventlog")


class AnonymizationType(StrEnum):
    lpr = "lpr"  # anonymize to "***AB"
    medium = "medium"  # anonymize if linked to a session
    default = "default"  # anonymize ":anonymize:" -> display with anonymize icon
    no = "no"


class PlateFormatData(OpenModuleModel):
    plate: str
    country: str | None = None


class MessageKwarg(OpenModuleModel):
    value: PlateFormatData | int | float | bool | str
    anonymization_type: AnonymizationType = AnonymizationType.default
    format_type: str

    @staticmethod
    def lpr(plate: str, country: str | None = None):
        return MessageKwarg(value=PlateFormatData(plate=plate, country=country or "-"), format_type="lpr",
                            anonymization_type=AnonymizationType.lpr)

    @staticmethod
    def medium(value: str):
        return MessageKwarg(value=value, format_type="medium", anonymization_type=AnonymizationType.medium)

    @staticmethod
    def string(value: str):
        return MessageKwarg(value=value, format_type="string", anonymization_type=AnonymizationType.default)

    @staticmethod
    def price(cents: int):
        return MessageKwarg(value=cents, format_type="price", anonymization_type=AnonymizationType.no)

    @staticmethod
    def rate(rate_id: str):
        return MessageKwarg(value=rate_id, format_type="rate", anonymization_type=AnonymizationType.no)

    @staticmethod
    def cost_group(cost_group: str):
        return MessageKwarg(value=cost_group, format_type="cost_group", anonymization_type=AnonymizationType.no)

    @staticmethod
    def gate(technical_name: str):
        return MessageKwarg(value=technical_name, format_type="gate", anonymization_type=AnonymizationType.no)

    @model_validator(mode="after")
    def check_value_type_to_format_type(self) -> Self:
        match self.format_type:
            case "lpr":
                assert isinstance(self.value, PlateFormatData), "lpr has to be PlateFormatData" 
            case "medium":
                assert isinstance(self.value, str), "medium has to be str"
            case "string":
                assert isinstance(self.value, str), "string has to be str"
            case "price":
                assert isinstance(self.value, int), "price has to be int"
            case "gate":
                assert isinstance(self.value, str), "gate has to be str"
            case _:
                # extend if more format_types are added
                pass
        return self


class EventInfo(OpenModuleModel):
    type: str  # a category for icons and grouping, must contain at least one "_", hierarchy via prefix
    timestamp: Datetime
    gate: str | None = None
    license_plate: str | None = None  # anonymized with type lpr
    license_plate_country: str | None = None
    session_id: str | None = None
    related_session_id: str | None = None
    vehicle_id: str | None = None
    price: int | None = None  # cents

    @field_validator("type")
    @classmethod
    def type_contains_underscore(cls, v):
        assert "_" in v, "type must container at least one underscore"
        return v

    @staticmethod
    def create(type: str, timestamp: datetime | None = None, gate: str | None = None,
               license_plate: str | None = None, license_plate_country: str | None = None,
               session_id: str | None = None, related_session_id: str | None = None,
               vehicle_id: str | None = None, price: int | None = None):
        return EventInfo(type=type, timestamp=timestamp or utcnow(), gate=gate, license_plate=license_plate,
                         license_plate_country=license_plate_country, session_id=session_id,
                         related_session_id=related_session_id, vehicle_id=vehicle_id, price=price)


class Event(OpenModuleModel):
    message: str  # e.g. 'Session with license plate {lpr} at entry "Einfahrt" started.'
    message_kwargs: dict[str, MessageKwarg]  # e.g. {"lpr": }
    infos: EventInfo


class EventlogMessage(ZMQMessage):
    type: str = "create_event"
    event: Event

    def send(self):
        """publish the message with the core publisher on the eventlog topic"""
        core().publish(self, "eventlog")

    @staticmethod
    def create(infos: EventInfo, message: str, **message_kwargs: MessageKwarg):
        """create a new eventlog message with the given parameters"""
        return EventlogMessage(event=Event(infos=infos, message=message, message_kwargs=message_kwargs))


@sentry.trace
def send_event(infos: EventInfo, message: str, **message_kwargs: MessageKwarg):
    format_kwargs = {key: kwarg.value for key, kwarg in message_kwargs.items()}
    if infos.gate:
        log.info(f"Sending event at {infos.gate}: {message.format(**format_kwargs)}")
    else:
        log.info(f"Sending event: {message.format(**format_kwargs)}")
    EventlogMessage.create(infos=infos, message=message, **message_kwargs).send()

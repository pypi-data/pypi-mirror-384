import codecs
import csv
import dataclasses
import re
from datetime import datetime, timedelta, tzinfo
from decimal import Decimal
from enum import StrEnum
from time import gmtime, strftime
from typing import Iterable, Any, BinaryIO, Callable

from dateutil.tz import UTC, gettz
from pydantic import TypeAdapter
from openmodule.utils.schedule import Scheduler

from openmodule import sentry
from openmodule.config import settings
import hashlib


def schedule_export(offset_minutes, scheduler: Scheduler | None = None, callback: Callable | None = None) -> int:
    """
    Generates a randomized export time for exports.
    The time depends on the constant given offset and a randomized offset (<1h) based on the resource.
    The randomized offset is constant for the same resource.
    If a scheduler and callback are given, the callback is also scheduled daily for the calculated time.
    """

    assert offset_minutes < 60, "Offset must be smaller than 60 minutes"

    resource_hash = hashlib.sha256(settings.RESOURCE.encode("utf-8")).hexdigest()
    random_offset = int(resource_hash, 16) % 60

    offset = offset_minutes + random_offset
    if scheduler and callback:
        upload_time = strftime("%H:%M", gmtime(offset * 60))
        scheduler.every().day.at(upload_time, settings.TIMEZONE).do(callback)
    return offset


class CsvFormatType(StrEnum):
    static_text = "static_text"
    """just inserts static text"""

    string = "string"
    """no reformatting, works for str, int (e.g. for vehicle_id) and enum"""

    number = "number"
    """correct seperator for floating point values, works for int, float, Decimal and bool"""

    percentage = "percentage"
    """added % and correct seperator for floating point values. Does NOT divide by 100. 
    works for float, int and Decimal"""

    datetime = "datetime"
    """converts into specified timezone and prints as iso string. Works for datetime"""

    duration = "duration"
    """formats as HH:MM::SS. Works for timedelta"""

    currency_amount = "currency_amount"
    """formats Cent amounts into € with 2 decimal places (or equivalent for other currencies). 
    does NOT add currency symbol"""


_NUMBER_REGEX = re.compile(r"^\s*-[*\s.,\d]*$")
_PHONE_REGEX = re.compile(r"^\s*\+[*\s\d\(\)]*$")

# some constants which might be turned into parameters later
_COMMA_SEPARATOR = ","
_DATETIME_FORMAT = "%d.%m.%Y %H:%M:%S"
_ENCODING = "utf-16-le"
_ENCODING_CODEC = codecs.BOM_UTF16_LE


def _format_static_text(value: str | StrEnum) -> str:
    assert isinstance(value, str), "Static text columns allow only str or enum"
    return _format_string(value)


def _format_string(value: str | StrEnum) -> str:
    assert isinstance(value, str) or isinstance(value, int), "String columns allow only str and string enum"
    if isinstance(value, str):
        assert all(bad_char not in value for bad_char in ["\x0d", "\x09"]), \
            'Forbidden chars "\\x0d" or "\\x09" in string'
        assert not value or value[0] not in "=@", 'String must not start with "=" or "@"'
        assert (value and value[0]) != "+" or _PHONE_REGEX.match(value), \
            'Strings starting with "+" must be phone numbers'
        assert (value and value[0]) != "-" or _NUMBER_REGEX.match(value), 'Strings starting with "-" must be numbers'
    else:
        value = str(value)
    return value


def _format_number(value: int | float | bool | Decimal) -> str:
    assert any(isinstance(value, t) for t in [int, float, bool, Decimal]), \
        "Number columns allow only int, float, bool, Decimal"
    if isinstance(value, bool):
        value = int(value)
    return str(value).replace(".", _COMMA_SEPARATOR)


def _format_percentage(value: int | float | Decimal) -> str:
    assert any(isinstance(value, t) for t in [int, float, Decimal]), \
        "Percentage columns allow only int, float, Decimal"
    return str(value).replace(".", _COMMA_SEPARATOR) + "%"


def _format_datetime(value: datetime | str, timezone: tzinfo) -> str:
    assert isinstance(value, datetime) or isinstance(value, str), "Datetime columns allow only datetime and str"
    if isinstance(value, str):
        value = TypeAdapter(datetime).validate_strings(value)
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:  # is naive -> assume UTC
        value = value.replace(tzinfo=UTC)
    return value.astimezone(timezone).strftime(_DATETIME_FORMAT)


def _format_duration(value: timedelta | int | float) -> str:
    assert any(isinstance(value, t) for t in [timedelta, int, float]), \
        "Duration columns allow only timedelta, int and float"
    if isinstance(value, timedelta):
        value = int(value.total_seconds())
    elif isinstance(value, float):
        value = int(value)
    return f"{value // 3600:d}:{(value % 3600) // 60:02d}:{value % 60:02d}"


def _format_currency_amount(value: int) -> str:
    assert isinstance(value, int), "Currency amount columns allow only int"
    value = Decimal(value) / Decimal(100.)
    return f"{value:.2f}".replace(".", _COMMA_SEPARATOR)


class ColumnDefinition:
    def __init__(self, name: str, field_name: str, format_type: CsvFormatType, default_value: Any = None):
        self.name = name
        self.field_name = field_name
        self.format_type = format_type
        self.default_value = default_value


def _render_row(writer, row: dict | object, column_definitions: list[ColumnDefinition], timezone: tzinfo):
    values = []
    if not isinstance(row, dict):
        row = row.__dict__
    for column in column_definitions:
        value = row.get(column.field_name) if column.format_type != CsvFormatType.static_text else None
        if value is None:
            value = column.default_value
        if value is None:
            values.append(None)
        elif column.format_type == CsvFormatType.static_text:
            values.append(_format_static_text(column.default_value))
        elif column.format_type == CsvFormatType.string:
            values.append(_format_string(value))
        elif column.format_type == CsvFormatType.number:
            values.append(_format_number(value))
        elif column.format_type == CsvFormatType.percentage:
            values.append(_format_percentage(value))
        elif column.format_type == CsvFormatType.datetime:
            values.append(_format_datetime(value, timezone))
        elif column.format_type == CsvFormatType.duration:
            values.append(_format_duration(value))
        elif column.format_type == CsvFormatType.currency_amount:
            values.append(_format_currency_amount(value))
    writer.writerow(values)


@sentry.trace
def render(file_object: BinaryIO, data: Iterable[dict | object], column_definitions: list[ColumnDefinition],
           timezone: str = settings.TIMEZONE):
    """
    Renders the data into csv based on column_definitions. If output_fn is given it's rendered directly into file
    otherwise bytearray is returned
    :param file_object: File like object to write csv into (binary write)
    :param data: Iterable of dicts or objects containing data for csv
    :param column_definitions: Defining columns with name, format_type and where data is in objects/dicts
    :param timezone: timezone into which datetime columns are converted
    """

    timezone_obj = gettz(timezone)
    if timezone_obj is None:
        raise ValueError(f"{timezone} is no valid timezone")
    file_object.write(_ENCODING_CODEC)
    out_stream = codecs.getwriter(_ENCODING)(file_object)
    writer = csv.writer(out_stream, quoting=csv.QUOTE_ALL, delimiter="\t")
    headers = [column.name for column in column_definitions]
    writer.writerow(headers)
    for row in data:
        _render_row(writer, row, column_definitions, timezone_obj)


@dataclasses.dataclass
class ExportIterator:
    """
    Filter your database with:
      created >= utc_start && created < utc_end

    All datetime objects are naive
    """
    csv_date_string: str  # e.g. 2023-12-30
    local_start: datetime  # local start datetime, most likely just used for logs/events, e.g. 2023-12-30 00:00:00
    local_end: datetime  # local end datetime (not inclusive), e.g. 2023-12-31 00:00:00
    utc_start: datetime  # utc start datetime, most likely to be used for filtering events in your DB
    utc_end: datetime  # utc end datetime (not inclusive) to be used for filtering events in your DB


def export_iterator(timezone: tzinfo, utc_last_export_start: datetime | None,
                    utc_min_event_time: datetime | None) -> Iterable[ExportIterator]:
    """
    Returns an iterator for creating exports. For every returned ExportIterator object you should generate an export
    for that day. It requires the following naive datetime objects in UTC timezone:

    param utc_last_export_start: The last export start time in UTC, it MUST be 00:00:00 in local time (which it is if
                                 you use the utc_start from the previous ExportIterator)

    param utc_min_event_time: The first time you have recorded any event in your system in utc. This is used to
                              determine the first export date, if your system has not made exports for some time
                              and earlier data exists.
    """
    assert utc_last_export_start is None or utc_last_export_start.tzinfo is None, "utc_last_export_start must be naive and in UTC timezone"
    assert utc_min_event_time is None or utc_min_event_time.tzinfo is None, "utc_min_event_time must be naive and in UTC timezone"

    aware_local_now = datetime.now(UTC).astimezone(timezone)

    if utc_last_export_start is not None:
        last_local_start = utc_last_export_start.replace(tzinfo=UTC).astimezone(timezone)
        assert last_local_start.hour == last_local_start.minute == last_local_start.second == last_local_start.microsecond == 0, (
            "Your last export start was not at midnight. Did you save the correct timestamp to the database?."
        )

        aware_local_start = last_local_start + timedelta(days=1)
    else:
        # fallback time of nothing has happened -> yesterday, so on the first day the system is running
        # at midnight we will export an empty file for the first day
        fallback_time = (aware_local_now - timedelta(days=1)).astimezone(UTC).replace(tzinfo=None)

        utc_min_event_time = utc_min_event_time or fallback_time
        local_min_event_time = utc_min_event_time.replace(tzinfo=UTC).astimezone(timezone)
        aware_local_start = local_min_event_time.replace(hour=0, minute=0, second=0, microsecond=0)

    while True:
        aware_local_end = aware_local_start + timedelta(days=1)
        if aware_local_end > aware_local_now:
            break
        yield ExportIterator(
            csv_date_string=aware_local_start.strftime("%Y-%m-%d"),
            local_start=aware_local_start.replace(tzinfo=None),
            local_end=aware_local_end.replace(tzinfo=None),
            utc_start=aware_local_start.astimezone(UTC).replace(tzinfo=None),
            utc_end=aware_local_end.astimezone(UTC).replace(tzinfo=None),
        )
        aware_local_start += timedelta(days=1)

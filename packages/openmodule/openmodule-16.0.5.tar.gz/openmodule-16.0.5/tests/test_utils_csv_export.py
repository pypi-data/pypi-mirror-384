from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO
from typing import Iterable
from unittest import TestCase

import freezegun
from dateutil.parser import parse
from dateutil.tz import gettz

from openmodule.config import settings, override_settings, override_context
from openmodule.utils.csv_export import render, ColumnDefinition, CsvFormatType, _ENCODING, _ENCODING_CODEC, \
    schedule_export, export_iterator


class CsvExportTest(TestCase):
    def render(self, data: Iterable[dict | object], column_definitions: list[ColumnDefinition],
               timezone: str = settings.TIMEZONE):
        stream = BytesIO()
        render(stream, data, column_definitions, timezone)
        return stream.getvalue().decode(_ENCODING)

    def test_default_value(self):
        columns = [ColumnDefinition(name="A", field_name="a", format_type=CsvFormatType.number),
                   ColumnDefinition(name="B", field_name="b", format_type=CsvFormatType.number, default_value=0)]
        # column with default value and missing field -> default value
        data = self.render([dict(a=8)], columns)
        self.assertIn('"A"\t"B"', data)
        self.assertIn('"8"\t"0"', data)

        # column with default value and None value -> default value
        data = self.render([dict(a=8, b=None)], columns)
        self.assertIn('"A"\t"B"', data)
        self.assertIn('"8"\t"0"', data)

        # column without default value -> ""
        data = self.render([dict()], columns)
        self.assertIn('"A"\t"B"', data)
        self.assertIn('""\t"0"', data)

    def test_incorrect_default_value(self):
        columns = [ColumnDefinition(name="A", field_name="a", format_type=CsvFormatType.number),
                   ColumnDefinition(name="B", field_name="b", format_type=CsvFormatType.number, default_value="a")]
        with self.assertRaises(AssertionError) as e:
            self.render([dict(a=8)], columns)
        self.assertIn("Number columns allow only int, float, bool, Decimal", str(e.exception))

    def test_static_field(self):
        columns = [ColumnDefinition(name="value", field_name="", format_type=CsvFormatType.static_text,
                                    default_value=123)]

        with self.assertRaises(AssertionError) as e:
            self.render([{}], columns)
        self.assertIn("Static text columns allow only str or enum", str(e.exception))

        columns = [ColumnDefinition(name="value", field_name="", format_type=CsvFormatType.static_text,
                                    default_value="test")]
        data = self.render([dict()], columns)
        self.assertIn('value"\r\n"test"\r\n', data)

    def test_string_field(self):
        columns = [ColumnDefinition(name="value", field_name="value", format_type=CsvFormatType.string)]
        with self.assertRaises(AssertionError) as e:
            self.render([dict(value=type)], columns)
        self.assertIn("String columns allow only str and string enum", str(e.exception))

        with self.assertRaises(AssertionError) as e:
            self.render([dict(value="test\x0dexample")], columns)
        self.assertIn('Forbidden chars "\\x0d" or "\\x09" in string', str(e.exception))

        with self.assertRaises(AssertionError) as e:
            self.render([dict(value="=test")], columns)
        self.assertIn('String must not start with "=" or "@"', str(e.exception))

        with self.assertRaises(AssertionError) as e:
            self.render([dict(value="+test")], columns)
        self.assertIn('Strings starting with "+" must be phone numbers', str(e.exception))

        data = self.render([dict(value="+43 664 12345678")], columns)
        self.assertIn('value"\r\n"+43 664 12345678"\r\n', data)

        data = self.render([dict(value=1)], columns)
        self.assertIn('value"\r\n"1"\r\n', data)

        data = self.render([dict(value="asdf@=")], columns)
        self.assertIn('value"\r\n"asdf@="\r\n', data)

    def test_number_field(self):
        columns = [ColumnDefinition(name="value", field_name="value", format_type=CsvFormatType.number)]

        with self.assertRaises(AssertionError) as e:
            self.render([dict(value="a")], columns)
        self.assertIn("Number columns allow only int, float, bool, Decimal", str(e.exception))

        data = self.render([dict(value=1)], columns)
        self.assertIn('value"\r\n"1"\r\n', data)

        data = self.render([dict(value=1.2)], columns)
        self.assertIn('value"\r\n"1,2"\r\n', data)

        data = self.render([dict(value=True)], columns)
        self.assertIn('value"\r\n"1"\r\n', data)

        data = self.render([dict(value=Decimal("10.12"))], columns)
        self.assertIn('value"\r\n"10,12"\r\n', data)

    def test_percentage_field(self):
        columns = [ColumnDefinition(name="value", field_name="value", format_type=CsvFormatType.percentage)]

        with self.assertRaises(AssertionError) as e:
            self.render([dict(value="a")], columns)
        self.assertIn("Percentage columns allow only int, float, Decimal", str(e.exception))

        data = self.render([dict(value=1)], columns)
        self.assertIn('value"\r\n"1%"\r\n', data)

        data = self.render([dict(value=1.2)], columns)
        self.assertIn('value"\r\n"1,2%"\r\n', data)

        data = self.render([dict(value=Decimal("10.12"))], columns)
        self.assertIn('value"\r\n"10,12%"\r\n', data)

    def test_datetime_field(self):
        columns = [ColumnDefinition(name="value", field_name="value", format_type=CsvFormatType.datetime)]
        with self.assertRaises(AssertionError) as e:
            self.render([dict(value=1)], columns)
        self.assertIn("Datetime columns allow only datetime and str", str(e.exception))
        with self.assertRaises(Exception) as e:
            self.render([dict(value="a")], columns)

        # aware datetime
        timestamp = datetime(2018, 1, 1, 12, 0, 1, tzinfo=gettz(settings.TIMEZONE))
        data = self.render([dict(value=timestamp)], columns)
        self.assertIn(f'value"\r\n"01.01.2018 12:00:01"\r\n', data)

        # utc datetime
        timestamp_utc = timestamp.astimezone(gettz('UTC')).replace(tzinfo=None)
        data = self.render([dict(value=timestamp_utc)], columns)
        self.assertIn(f'value"\r\n"01.01.2018 12:00:01"\r\n', data)

        data = self.render([dict(value=timestamp.isoformat())], columns)
        self.assertIn(f'value"\r\n"01.01.2018 12:00:01"\r\n', data)

        data = self.render([dict(value=timestamp_utc.isoformat())], columns)
        self.assertIn(f'value"\r\n"01.01.2018 12:00:01"\r\n', data)

        data = self.render([dict(value=timestamp_utc)], columns, "UTC")
        self.assertIn(f'value"\r\n"01.01.2018 11:00:01"\r\n', data)  # 11 because of winter

    def test_duration_field(self):
        columns = [ColumnDefinition(name="value", field_name="value", format_type=CsvFormatType.duration)]
        with self.assertRaises(AssertionError) as e:
            self.render([dict(value="a")], columns)
        self.assertIn("Duration columns allow only timedelta, int and float", str(e.exception))

        data = self.render([dict(value=10)], columns)
        self.assertIn(f'value"\r\n"0:00:10"\r\n', data)

        data = self.render([dict(value=12.1)], columns)
        self.assertIn(f'value"\r\n"0:00:12"\r\n', data)

        data = self.render([dict(value=timedelta(hours=12345, minutes=53, seconds=10, milliseconds=125))], columns)
        self.assertIn(f'value"\r\n"12345:53:10"\r\n', data)

    def test_currency_field(self):
        columns = [ColumnDefinition(name="value", field_name="value", format_type=CsvFormatType.currency_amount)]
        with self.assertRaises(AssertionError) as e:
            self.render([dict(value=123.45)], columns)
        self.assertIn("Currency amount columns allow only int", str(e.exception))

        data = self.render([dict(value=123)], columns)
        self.assertIn(f'value"\r\n"1,23"\r\n', data)

    def test_encoding(self):
        columns = [ColumnDefinition(name="value", field_name="value", format_type=CsvFormatType.string)]
        stream = BytesIO()
        render(stream, [dict(value="ÄÖÜß")], columns)
        data = stream.getvalue()
        self.assertEqual(data[:2], _ENCODING_CODEC)
        self.assertIn("ÄÖÜß".encode(_ENCODING), data)


@override_settings(RESOURCE="asdf")
class ExportTimeTest(TestCase):
    def cb(self):
        pass

    def test_error(self):
        with self.assertRaises(AssertionError) as e:
            schedule_export(571)
        self.assertIn("Offset must be smaller than 60 minutes", str(e.exception))

    def test_constant_for_resource(self):
        offset = schedule_export(0)
        offset1 = schedule_export(0)

        self.assertEqual(offset, offset1)

        with override_context(RESOURCE="bsdf"):
            offset2 = schedule_export(0)
            self.assertNotEqual(offset, offset2)


class ExportIteratorTest(TestCase):
    tz_vienna = gettz('Europe/Vienna')
    tz_london = gettz('Europe/London')
    tz_azores = gettz('Atlantic/Azores')

    def test_no_data_generates_no_exports(self):
        with freezegun.freeze_time("2023-01-01T01:00:00+02:00"):
            # None, None generate export for yesterday
            exports = list(export_iterator(self.tz_vienna, None, None))
            self.assertEqual(1, len(exports))
            self.assertEqual("2022-12-31", exports[0].csv_date_string)

        # future dates do not generate exports, i don't know if this is a feature or a bug,
        # but i wanted to test what happens, and this is what currently happens
        with freezegun.freeze_time("2023-01-01T00:00:00Z"):
            future_start = parse("2023-07-01T22:00:00")
            self.assertEqual(0, len(list(export_iterator(self.tz_vienna, future_start, None))))
            self.assertEqual(0, len(list(export_iterator(self.tz_vienna, None, future_start))))

    def test_dst_change_1(self):
        # tests what happens when we generate multiple exports on 1 run across dst change
        with freezegun.freeze_time("2023-03-28T02:00:00+02:00"):
            start = parse("2023-03-24T10:00:00")

            result = list(export_iterator(self.tz_vienna, None, start))

            # first event was somewhere on the 24th, so we export the 24th, 25th, 26th, 27th
            # and not today which is the 28th
            self.assertEqual(4, len(result))

            # the local timediff is always 24 hours
            self.assertEqual(1, (result[0].local_end - result[0].local_start).days)
            self.assertEqual(1, (result[1].local_end - result[1].local_start).days)
            self.assertEqual(1, (result[2].local_end - result[2].local_start).days)
            self.assertEqual(1, (result[3].local_end - result[3].local_start).days)

            # in utc one day has only 23 hours, as DST jumped 1 hour
            self.assertEqual(0, (result[2].utc_end - result[2].utc_start).days)
            self.assertEqual(23 * 3600, (result[2].utc_end - result[2].utc_start).total_seconds())

            # for the dst change check all data exactly
            self.assertEqual(parse("2023-03-25T23:00:00"), result[1].utc_end)
            self.assertEqual(parse("2023-03-25T23:00:00"), result[2].utc_start)
            self.assertEqual(parse("2023-03-26T22:00:00"), result[2].utc_end)
            self.assertEqual(parse("2023-03-26T22:00:00"), result[3].utc_start)
            self.assertEqual(parse("2023-03-26T00:00:00"), result[2].local_start)
            self.assertEqual(parse("2023-03-27T00:00:00"), result[2].local_end)
            self.assertEqual("2023-03-26", result[2].csv_date_string)

    def test_dst_change_2(self):
        # same test as above, but simulate what happens when we iteratively generate exports
        min_event = parse("2023-03-24T10:00:00")
        last_export = None
        results = []

        def _run_export():
            exports = list(export_iterator(self.tz_vienna, last_export, min_event))
            self.assertEqual(1, len(exports))
            export = exports[0]
            results.append(export)
            return export

        with freezegun.freeze_time("2023-03-25T01:58:00+01:00"):
            export = _run_export()
            last_export = export.utc_start

        with freezegun.freeze_time("2023-03-26T01:59:00+01:00"):
            export = _run_export()
            last_export = export.utc_start

        with freezegun.freeze_time("2023-03-27T01:59:00+02:00"):
            export = _run_export()
            last_export = export.utc_start

        with freezegun.freeze_time("2023-03-28T01:59:00+02:00"):
            export = _run_export()
            last_export = export.utc_start

        # first event was somewhere on the 24th, so we export the 24th, 25th, 26th, 27th
        # and not today which is the 28th
        self.assertEqual(4, len(results))

        # the local timediff is always 24 hours
        self.assertEqual(1, (results[0].local_end - results[0].local_start).days)
        self.assertEqual(1, (results[1].local_end - results[1].local_start).days)
        self.assertEqual(1, (results[2].local_end - results[2].local_start).days)
        self.assertEqual(1, (results[2].local_end - results[2].local_start).days)

        # in utc one day has only 23 hours, as DST jumped 1 hour
        self.assertEqual(0, (results[2].utc_end - results[2].utc_start).days)
        self.assertEqual(23 * 3600, (results[2].utc_end - results[2].utc_start).total_seconds())

        # for the dst change check all data exactly
        self.assertEqual(parse("2023-03-25T23:00:00"), results[1].utc_end)
        self.assertEqual(parse("2023-03-25T23:00:00"), results[2].utc_start)
        self.assertEqual(parse("2023-03-26T22:00:00"), results[2].utc_end)
        self.assertEqual(parse("2023-03-26T22:00:00"), results[3].utc_start)

        self.assertEqual(parse("2023-03-26T00:00:00"), results[2].local_start)
        self.assertEqual(parse("2023-03-27T00:00:00"), results[2].local_end)
        self.assertEqual("2023-03-26", results[2].csv_date_string)

    def test_dst_change_3(self):
        # test what happens when we generate exports in the time when its 02:00 o'clock twice
        min_event = parse("2023-10-27T10:00:00")
        last_export = None
        results = []

        def _run_export():
            exports = list(export_iterator(self.tz_vienna, last_export, min_event))
            self.assertEqual(1, len(exports))
            export = exports[0]
            results.append(export)
            return export

        with freezegun.freeze_time("2023-10-28T02:30:00+01:00"):
            export = _run_export()
            last_export = export.utc_start

        with freezegun.freeze_time("2023-10-29T02:30:00+01:00"):
            export = _run_export()
            last_export = export.utc_start

            # re running at the same time should obviously not generate a new export
            self.assertEqual(0, len(list(export_iterator(self.tz_vienna, last_export, min_event))))

        with freezegun.freeze_time("2023-10-29T02:30:00+02:00"):
            # re running now at the same (but different) time, 1 hour later
            self.assertEqual(0, len(list(export_iterator(self.tz_vienna, last_export, min_event))))

        with freezegun.freeze_time("2023-10-30T02:30:00+02:00"):
            export = _run_export()
            last_export = export.utc_start

        with freezegun.freeze_time("2023-10-31T02:30:00+02:00"):
            export = _run_export()
            last_export = export.utc_start


        self.assertEqual(4, len(results))

        # the local timediff is always 24 hours
        self.assertEqual(1, (results[0].local_end - results[0].local_start).days)
        self.assertEqual(1, (results[1].local_end - results[1].local_start).days)
        self.assertEqual(1, (results[2].local_end - results[2].local_start).days)
        self.assertEqual(1, (results[3].local_end - results[3].local_start).days)

        # in utc one day has 25 hours, as DST jumped back 1 hour
        self.assertEqual(1, (results[2].utc_end - results[2].utc_start).days)
        self.assertEqual(25 * 3600, (results[2].utc_end - results[2].utc_start).total_seconds())

        # for the dst change check all data exactly
        self.assertEqual(parse("2023-10-28T22:00:00"), results[1].utc_end)
        self.assertEqual(parse("2023-10-28T22:00:00"), results[2].utc_start)
        self.assertEqual(parse("2023-10-29T23:00:00"), results[2].utc_end)
        self.assertEqual(parse("2023-10-29T23:00:00"), results[3].utc_start)

        self.assertEqual(parse("2023-10-29T00:00:00"), results[2].local_start)
        self.assertEqual(parse("2023-10-30T00:00:00"), results[2].local_end)
        self.assertEqual("2023-10-29", results[2].csv_date_string)

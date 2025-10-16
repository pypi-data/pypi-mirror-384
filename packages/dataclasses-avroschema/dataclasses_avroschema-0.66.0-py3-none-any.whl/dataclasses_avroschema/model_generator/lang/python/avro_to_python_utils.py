import datetime
import typing

from dataclasses_avroschema.fields import field_utils

from . import templates

AVRO_TYPE_TO_PYTHON: typing.Dict[str, str] = {
    field_utils.NULL: "None",
    field_utils.BOOLEAN: "bool",
    field_utils.LONG: "int",
    field_utils.DOUBLE: "float",
    field_utils.BYTES: "bytes",
    field_utils.STRING: "str",
    field_utils.INT: "types.Int32",
    field_utils.FLOAT: "types.Float32",
    field_utils.DATE: "datetime.date",
    field_utils.TIME_MILLIS: "datetime.time",
    field_utils.TIME_MICROS: "types.TimeMicro",
    field_utils.TIMESTAMP_MILLIS: "datetime.datetime",
    field_utils.TIMESTAMP_MICROS: "types.DateTimeMicro",
    field_utils.TIMEDELTA: "datetime.timedelta",
    field_utils.UUID: "uuid.UUID",
}

LOGICAL_TYPES_IMPORTS: typing.Dict[str, str] = {
    field_utils.DECIMAL: "import decimal",
    field_utils.DATE: "import datetime",
    field_utils.TIMEDELTA: "import datetime",
    field_utils.TIME_MILLIS: "import datetime",
    field_utils.TIME_MICROS: "from dataclasses_avroschema import types",
    field_utils.TIMESTAMP_MILLIS: "import datetime",
    field_utils.TIMESTAMP_MICROS: "from dataclasses_avroschema import types",
    field_utils.UUID: "import uuid",
}

# Avro types to python types
LOGICAL_TYPES_TO_PYTHON = {
    field_utils.DATE: lambda value: datetime.date.fromordinal(value + (datetime.date(1970, 1, 1).toordinal())),
    field_utils.TIME_MILLIS: lambda value: (datetime.datetime.min + datetime.timedelta(milliseconds=value)).time(),
    field_utils.TIME_MICROS: lambda value: (datetime.datetime.min + datetime.timedelta(microseconds=value)).time(),
    field_utils.TIMESTAMP_MILLIS: lambda value: datetime.datetime.fromtimestamp(value / 1000, tz=datetime.timezone.utc),
    field_utils.TIMESTAMP_MICROS: lambda value: datetime.datetime.fromtimestamp(
        value / 1000000, tz=datetime.timezone.utc
    ),
    field_utils.TIMEDELTA: lambda value: datetime.timedelta(seconds=value),
}

# Logical types objects to template
LOGICAL_TYPE_TEMPLATES = {
    field_utils.DATE: lambda date_obj: templates.date_template.safe_substitute(
        year=date_obj.year, month=date_obj.month, day=date_obj.day
    ),
    field_utils.TIME_MILLIS: lambda time_obj: templates.time_template.safe_substitute(
        hour=time_obj.hour, minute=time_obj.minute, second=time_obj.second
    ),
    field_utils.TIME_MICROS: lambda time_obj: templates.time_micros_template.safe_substitute(
        hour=time_obj.hour,
        minute=time_obj.minute,
        second=time_obj.second,
        microsecond=time_obj.microsecond,
    ),
    field_utils.TIMESTAMP_MILLIS: lambda datetime_obj: templates.datetime_template.safe_substitute(
        year=datetime_obj.year,
        month=datetime_obj.month,
        day=datetime_obj.day,
        hour=datetime_obj.hour,
        minute=datetime_obj.minute,
        second=datetime_obj.second,
    ),
    field_utils.TIMESTAMP_MICROS: lambda datetime_obj: templates.datetime_micros_template.safe_substitute(
        year=datetime_obj.year,
        month=datetime_obj.month,
        day=datetime_obj.day,
        hour=datetime_obj.hour,
        minute=datetime_obj.minute,
        second=datetime_obj.second,
        microsecond=datetime_obj.microsecond,
    ),
    field_utils.TIMEDELTA: lambda timedelta_obj: templates.timedelta_template.safe_substitute(
        seconds=timedelta_obj.total_seconds(),
    ),
}


def render_datetime(*, value: int, format: str) -> str:
    fn = LOGICAL_TYPES_TO_PYTHON[format]
    datetime_obj = fn(value)

    template = LOGICAL_TYPE_TEMPLATES[format]
    return template(datetime_obj)

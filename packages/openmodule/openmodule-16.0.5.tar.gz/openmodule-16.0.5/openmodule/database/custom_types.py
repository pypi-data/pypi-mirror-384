from datetime import datetime

import orjson
from sqlalchemy import DateTime
from sqlalchemy import VARCHAR
from sqlalchemy.types import TypeDecorator


class CustomTypeImportRegistration(type):
    """
    This metaclass is used to register custom types with their module names.
    This is used in generating alembic migrations.
    """

    def __new__(cls, name, bases, dct):
        x = super().__new__(cls, name, bases, dct)

        if len(bases) == 1:
            if not getattr(bases[0], "_registry", None):
                setattr(bases[0], "_registry", dict())
            bases[0]._registry[x] = x.__module__
        return x


class CustomType(TypeDecorator, metaclass=CustomTypeImportRegistration):
    @classmethod
    def custom_import(cls, obj):
        for custom, mod in cls._registry.items():
            if type(obj) == custom:
                return mod, custom.__name__
        return None, None


class TZDateTime(CustomType):
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            assert not isinstance(value, datetime) or value.tzinfo is None, (
                "You need to convert a datetime to a naive time, because sqlite loses tz infos. "
            )
        return value


class JSONEncodedDict(CustomType):
    impl = VARCHAR
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = orjson.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = orjson.loads(value)
        return value

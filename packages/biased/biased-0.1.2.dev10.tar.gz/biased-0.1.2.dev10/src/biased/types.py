from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network
from logging import getLevelNamesMapping
from typing import Annotated, Any
from uuid import UUID

import annotated_types
import ulid
from pydantic import AfterValidator, AnyUrl, BaseModel, BeforeValidator, PlainSerializer, StringConstraints, conint
from pydantic.json_schema import Examples, SkipJsonSchema
from pydantic_core import Url

from biased.utils.aba_routing_number import validate_aba_routing_number


class Empty: ...


AbaRoutingNumber = Annotated[
    str,
    StringConstraints(
        strict=True,
        strip_whitespace=True,
        min_length=9,
        max_length=9,
        pattern=r"^[0-9]{9}$",
    ),
    AfterValidator(validate_aba_routing_number),
]

DayOfMonth = conint(ge=1, le=31)


def _validate_calendar_month_day(value: date) -> date:
    if value.day != 1:
        raise ValueError("Day must be 1 for CalendarMonth")
    return value


def _try_validate_calendar_month(value: Any) -> date | Any:
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m").date()
        except ValueError:
            pass
    return value


def _serialize_calendar_month(value: date) -> str:
    return value.strftime("%Y-%m")


CalendarMonth = Annotated[
    date,
    BeforeValidator(_try_validate_calendar_month),
    AfterValidator(_validate_calendar_month_day),
    PlainSerializer(_serialize_calendar_month, return_type=str),
]

MoneyAmount = Annotated[Decimal, Examples([Decimal("1.23")])]
NonNegativeMoneyAmount = Annotated[MoneyAmount, annotated_types.Ge(0)]

ItemsPerPageLimit = Annotated[int, annotated_types.Ge(0), annotated_types.Le(100)]

AsciiStr = Annotated[str, StringConstraints(strict=True, pattern=r"^[ -~]*$")]

AlphanumStr = Annotated[str, StringConstraints(strict=True, pattern=r"^[a-zA-Z0-9]+$")]

JsonPrimitiveTypes = (
    str
    | int
    | float
    | bool
    | None
    # DjangoJSONEncoder:
    | SkipJsonSchema[UUID]
    | SkipJsonSchema[Decimal]
    | SkipJsonSchema[datetime]
    | SkipJsonSchema[date]
    | SkipJsonSchema[time]
    | SkipJsonSchema[timedelta]
    # Unable to generate pydantic-core schema for <class 'django.utils.functional.Promise'>
    # | SkipJsonSchema[Promise]
    # NinjaJSONEncoder:
    | SkipJsonSchema[Enum]
    | SkipJsonSchema[Url]
    | SkipJsonSchema[IPv4Address]
    | SkipJsonSchema[IPv4Network]
    | SkipJsonSchema[IPv6Address]
    | SkipJsonSchema[IPv6Network]
    # BiasedNinjaJSONEncoder:
    | SkipJsonSchema[BaseModel]
    | SkipJsonSchema[AnyUrl]
)
type JsonSerializable = dict[str, JsonSerializable] | list[JsonSerializable] | JsonPrimitiveTypes
JsonSerializableDict = dict[str, JsonSerializable]
FlatJsonSerializableDict = dict[str, JsonPrimitiveTypes]


def validate_log_level(v: int | str) -> int:
    if isinstance(v, str):
        levels = getLevelNamesMapping()
        try:
            return levels[v]
        except KeyError as e:
            raise ValueError(f'Invalid log level "{v}", valid values are: {", ".join(levels.keys())}') from e
    if not isinstance(v, int):
        raise ValueError(f'Invalid log level "{v}", value must be an integer or string')
    return v


LogLevel = Annotated[int, BeforeValidator(validate_log_level)]

UlidStr = Annotated[
    str,
    StringConstraints(
        strict=True,
        strip_whitespace=True,
        to_upper=True,
        min_length=26,
        max_length=26,
        pattern=r"^0[0-9A-HJKMNP-TV-Z]{25}$",
    ),
    AfterValidator(lambda x: ulid.parse(x).str),
    # This Examples annotation leads to "😱 Could not render Parameters, see the console." in Swagger
    # while rendering URL params, probably Django Ninja bug, uncomment when fixed
    # Examples(["01JXZEA2CWN5MF175CZATYGYWQ"]),
    # Works but leads to the same value everywhere
    # WithJsonSchema({'type': 'string', 'example': ulid.new().str})
]

NotEmptyString = Annotated[
    str,
    StringConstraints(
        strict=True,
        strip_whitespace=True,
        min_length=1,
    ),
]

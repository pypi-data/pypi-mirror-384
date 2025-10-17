from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from json import JSONEncoder
from uuid import UUID

from pydantic import AnyUrl, BaseModel
from ulid import ULID


def _is_aware(value: time):
    return value.utcoffset() is not None


def _get_duration_components(duration: timedelta):
    days = duration.days
    seconds = duration.seconds
    microseconds = duration.microseconds

    minutes = seconds // 60
    seconds %= 60

    hours = minutes // 60
    minutes %= 60

    return days, hours, minutes, seconds, microseconds


def _duration_iso_string(duration: timedelta):
    if duration < timedelta(0):
        sign = "-"
        duration *= -1
    else:
        sign = ""

    days, hours, minutes, seconds, microseconds = _get_duration_components(duration)
    ms = f".{microseconds:06d}" if microseconds else ""
    return f"{sign}P{days}DT{hours:02d}H{minutes:02d}M{seconds:02d}{ms}S"


class DefaultJsonEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat().replace("+00:00", "Z")
        if isinstance(o, date):
            return o.isoformat()
        if isinstance(o, time):
            if _is_aware(o):
                raise ValueError("JSON can't represent timezone-aware times.")
            r = o.isoformat()
            if o.microsecond:
                r = r[:12]
            return r
        if isinstance(o, timedelta):
            return _duration_iso_string(o)
        if isinstance(o, Decimal | UUID | ULID | AnyUrl):
            return str(o)
        if isinstance(o, BaseModel):
            return o.model_dump()
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, bytes):
            return o.decode()
        return super().default(o)

import ulid
from pydantic import TypeAdapter

from biased.types import UlidStr


def build_ulid_str() -> UlidStr:
    return ulid.new().str


def validate_ulid_str(value: str) -> UlidStr:
    return TypeAdapter(type=UlidStr).validate_python(value)

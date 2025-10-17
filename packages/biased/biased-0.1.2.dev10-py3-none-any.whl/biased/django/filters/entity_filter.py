from enum import StrEnum, auto, unique

from django.db.models import Q, Value
from pydantic import TypeAdapter, ValidationError

from biased.django.filters.input_filter import CommaSeparatedInputFilter
from biased.types import UlidStr


@unique
class ValueType(StrEnum):
    none = auto()
    int = auto()
    ulid = auto()
    str = auto()


def _parse_value(value: str) -> tuple[ValueType, int | UlidStr | str]:
    try:
        return ValueType.int, int(value)
    except ValueError:
        pass
    try:
        return ValueType.ulid, TypeAdapter(UlidStr).validate_python(value)
    except ValidationError:
        pass
    return ValueType.str, value.strip('"')


class EntityFilter(CommaSeparatedInputFilter):
    def int_value_to_filter(self, value: int) -> Q:
        return Q(Value(False))

    def ulid_value_to_filter(self, value: UlidStr) -> Q:
        return Q(Value(False))

    def str_value_to_filter(self, value: str) -> Q:
        return Q(Value(False))

    def value_to_filter(self, value: str) -> Q:
        value_type, parsed_value = _parse_value(value=value)
        if value_type == ValueType.int:
            return self.int_value_to_filter(value=parsed_value)
        if value_type == ValueType.ulid:
            return self.ulid_value_to_filter(value=parsed_value)
        if value_type == ValueType.str:
            return self.str_value_to_filter(value=parsed_value)
        raise NotImplementedError(f"{value_type} is not supported")

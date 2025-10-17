from collections.abc import Iterable
from enum import Enum

from django.db.models import TextChoices


def enum_to_choices(enum: type[Enum]) -> Iterable[tuple[str, str]]:
    return ((i.name, getattr(i.value, "label", i.value)) for i in enum)


def choices_to_text_choices(enum_name: str, choices: Iterable[tuple[str, str]]) -> TextChoices:
    attrs = {value: (value, label) for value, label in choices}
    return TextChoices(enum_name, attrs)

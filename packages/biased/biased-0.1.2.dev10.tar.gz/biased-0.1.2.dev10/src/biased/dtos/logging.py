import logging
from enum import StrEnum, auto, unique

from biased.dtos.base import BaseDto
from biased.types import LogLevel


@unique
class LogFormatter(StrEnum):
    json = auto()
    human = auto()


class LoggingParams(BaseDto):
    level: LogLevel = logging.INFO
    formatter: LogFormatter = LogFormatter.json
    levels: dict[str, LogLevel] = {}
    colors: bool = True

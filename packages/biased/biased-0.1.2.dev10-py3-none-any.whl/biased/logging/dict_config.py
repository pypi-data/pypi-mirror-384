from typing import cast

import structlog
from injector import inject

from biased.dtos.logging import LogFormatter, LoggingParams
from biased.logging.utils import structlog_json_serializer
from biased.structlog.processors import AsyncTaskInfoAdder


def _get_logging_dict_config(params: LoggingParams) -> dict:
    foreign_pre_chain = (structlog.stdlib.ExtraAdder(),)

    processors = (
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
        structlog.processors.CallsiteParameterAdder(
            parameters=(
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.MODULE,
                structlog.processors.CallsiteParameter.PROCESS,
                structlog.processors.CallsiteParameter.PROCESS_NAME,
                structlog.processors.CallsiteParameter.THREAD,
                structlog.processors.CallsiteParameter.THREAD_NAME,
            )
        ),
        AsyncTaskInfoAdder(),
        structlog.processors.StackInfoRenderer(),
        # structlog.processors.format_exc_info,
    )

    config: dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            LogFormatter.json.value: {
                "()": structlog.stdlib.ProcessorFormatter,
                "foreign_pre_chain": foreign_pre_chain,
                "processors": (
                    *processors,
                    structlog.processors.JSONRenderer(serializer=structlog_json_serializer),
                ),
            },
            LogFormatter.human.value: {
                "()": structlog.stdlib.ProcessorFormatter,
                "foreign_pre_chain": foreign_pre_chain,
                "processors": (
                    *processors,
                    structlog.dev.ConsoleRenderer(colors=params.colors),
                ),
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": params.formatter,
            },
        },
        "loggers": {
            "root": {
                "level": params.level,
                "handlers": ["console"],
            },
        },
    }

    loggers = cast(dict, config["loggers"])
    for logger_name, level in params.levels.items():
        if logger_name in loggers:
            loggers[logger_name]["level"] = level
        else:
            loggers[logger_name] = dict(level=level)
    return config


class LoggingDictConfig(dict):
    @inject
    def __init__(self, params: LoggingParams):
        super().__init__()
        self.update(_get_logging_dict_config(params=params))

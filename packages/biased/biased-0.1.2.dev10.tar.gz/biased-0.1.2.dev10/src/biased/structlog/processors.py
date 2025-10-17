import logging
from asyncio import current_task

from structlog.typing import EventDict


def get_async_task_info() -> dict:
    try:
        task = current_task()
    except RuntimeError:
        return {}

    return dict(
        async_task_name=task and task.get_name(),
        async_task=id(task),
    )


class AsyncTaskInfoAdder:
    def __call__(self, logger: logging.Logger, name: str, event_dict: EventDict) -> EventDict:
        event_dict.update(get_async_task_info())
        return event_dict

from collections.abc import Callable
from operator import attrgetter
from typing import Any


def attrgetter_default(*attrs, default: Any = None) -> Callable[[Any], Any]:
    def wrapper(obj: Any):
        try:
            return attrgetter(*attrs)(obj)
        except AttributeError:
            return default

    return wrapper

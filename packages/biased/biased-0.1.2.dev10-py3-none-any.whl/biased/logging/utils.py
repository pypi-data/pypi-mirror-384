import json

from biased.structlog.structlog_json_encoder import StructlogJsonEncoder


def structlog_json_serializer(*args, **kwargs) -> str:
    kwargs.pop("default")
    kwargs.update(dict(cls=StructlogJsonEncoder, sort_keys=True, separators=(",", ":")))
    return json.dumps(*args, **kwargs)

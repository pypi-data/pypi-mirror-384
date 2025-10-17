from django_redis.serializers.base import BaseSerializer
from pydantic import BaseModel


class PydanticSerializer(BaseSerializer):
    def dumps(self, value: BaseModel) -> bytes:
        return value.model_dump_json(exclude_unset=True).encode()

    def loads(self, value: bytes) -> bytes:
        return value

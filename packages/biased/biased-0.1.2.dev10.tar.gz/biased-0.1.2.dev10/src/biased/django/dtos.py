from typing import Any

from biased.dtos.env_file_paths import EnvFilePathsSettings


class DjangoSettings(EnvFilePathsSettings):
    def django_dump(self) -> dict[str, Any]:
        return {field_name: getattr(self, field_name) for field_name in type(self).model_fields.keys()}

from pydantic_settings import SettingsConfigDict

from biased.dtos.env_file_paths import EnvFilePathsSettings
from biased.dtos.logging import LoggingParams


class LoggingSettings(LoggingParams, EnvFilePathsSettings):
    model_config = SettingsConfigDict(extra="ignore", env_prefix="LOG_", env_nested_delimiter="__")

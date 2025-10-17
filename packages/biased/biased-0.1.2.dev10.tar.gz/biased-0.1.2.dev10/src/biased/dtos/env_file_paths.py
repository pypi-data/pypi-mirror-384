from injector import inject
from pydantic import RootModel
from pydantic_settings import BaseSettings
from pydantic_settings.sources import DotenvType

EnvFilePaths = RootModel[DotenvType | None]


class EnvFilePathsSettings(BaseSettings):
    @inject
    def __init__(self, env_file_paths: EnvFilePaths, **kwargs):
        super().__init__(_env_file=env_file_paths.root, **kwargs)

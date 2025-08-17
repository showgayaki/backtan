import json
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    NAME: str
    USER: str
    PASSWORD: str
    THRESHOLD_STORAGE_DAYS: int
    UPLOAD_FOLDER_ID: str


@dataclass
class AppConfig:
    DATABASES: list[DatabaseConfig]
    SSH_HOST: str
    EXEC_COMMAND: str
    EXEC_DIR: str
    TIME_ZONE: str


def _load_config() -> AppConfig:
    with open('config.json', 'r') as f:
        config = json.load(f)

    # DATABASES を DatabaseConfig インスタンスのリストに変換
    databases = [DatabaseConfig(**db) for db in config['DATABASES']]
    config['DATABASES'] = databases

    return AppConfig(**config)


class Config:
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._config = _load_config()
        return cls._instance

    @property
    def config(self):
        return self._config

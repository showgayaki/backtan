import json
from types import SimpleNamespace


def _load_config():
    with open('config.json', 'r') as f:
        config = json.load(f)

    return SimpleNamespace(**config)


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

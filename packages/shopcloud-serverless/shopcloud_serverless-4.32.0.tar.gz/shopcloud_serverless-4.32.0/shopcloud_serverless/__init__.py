import os
from pathlib import Path

from . import decorators  # noqa
from . import endpoints_utils  # noqa


class Environment:
    def __init__(self):
        self._data = self._read_env()

    def _read_env(self):
        env_data = {}
        if Path('.env').exists():
            with open('.env') as f:
                env_data = f.read().split('\n')
                env_data = {x.split('=')[0]: x.split('=')[1] for x in env_data if x}
        return env_data

    def get(self, key: str):
        return self._data.get(key, os.environ.get(key))

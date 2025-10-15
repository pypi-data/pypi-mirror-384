from time import time

from typing_extensions import Self

from ._abstract import AbstractDomainUpdatesManager


class TimeoutDomainUpdatesManager(AbstractDomainUpdatesManager):
    def __init__(self, timeout: int):
        self._timeout = timeout

        self._timestamp = None

    async def __aenter__(self):
        self._timestamp = time()
        return self

    async def __aexit__(self, __exc_type, __exc_value, __traceback):
        self._timestamp = None

    @property
    async def has_changed(self) -> bool:
        if self._timestamp is None:
            raise AttributeError
        return time() - self._timestamp < self._timeout

    async def update(self) -> None:
        if self._timestamp is None:
            raise AttributeError
        self._timestamp = time()

    @classmethod
    def from_config(cls, config: dict) -> Self:
        return cls(config.get('timeout', 60))

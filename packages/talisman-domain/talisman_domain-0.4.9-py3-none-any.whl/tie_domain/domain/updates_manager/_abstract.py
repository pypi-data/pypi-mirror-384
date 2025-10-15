from abc import ABCMeta, abstractmethod
from typing import AsyncContextManager

from typing_extensions import Self


class AbstractDomainUpdatesManager(AsyncContextManager, metaclass=ABCMeta):

    async def __aenter__(self):
        return self

    @property
    @abstractmethod
    async def has_changed(self) -> bool:
        pass

    @abstractmethod
    async def update(self) -> None:
        pass

    @classmethod
    @abstractmethod
    def from_config(cls, config: dict) -> Self:
        pass

from typing_extensions import Self

from ._abstract import AbstractDomainUpdatesManager


class NeverDomainUpdatesManager(AbstractDomainUpdatesManager):
    @property
    async def has_changed(self) -> bool:
        return False

    async def update(self) -> None:
        pass

    @classmethod
    def from_config(cls, config: dict) -> Self:
        return cls()

    async def __aexit__(self, __exc_type, __exc_value, __traceback):
        pass

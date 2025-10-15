from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field

from tp_interfaces.domain.abstract import AbstractRelExtBasedType, RelExtModel
from ._abstract import AbstractAdapterBasedType
from ._cached import CachedValue, cached


@dataclass(frozen=True)
class RelExtBasedType(AbstractAdapterBasedType, AbstractRelExtBasedType, metaclass=ABCMeta):
    _pretrained_relext_models: CachedValue[tuple[RelExtModel, ...]] = field(default_factory=CachedValue)

    def __post_init__(self):
        if not isinstance(self._pretrained_relext_models, CachedValue):
            raise ValueError
        AbstractAdapterBasedType.__post_init__(self)
        AbstractRelExtBasedType.__post_init__(self)

    @property
    @cached
    async def pretrained_relext_models(self) -> tuple[RelExtModel, ...]:
        type_ = await self._load_object()
        return tuple(RelExtModel(**model) for model in type_['pretrained_models'])

    @abstractmethod
    async def _load_object(self) -> dict:
        pass

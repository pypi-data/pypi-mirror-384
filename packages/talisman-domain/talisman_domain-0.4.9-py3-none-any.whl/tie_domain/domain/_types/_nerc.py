from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from itertools import chain

from tp_interfaces.domain.abstract import AbstractNERCBasedType, NERCRegexp
from ._abstract import AbstractAdapterBasedType
from ._cached import CachedValue, cached


@dataclass(frozen=True)
class NERCBasedType(AbstractAdapterBasedType, AbstractNERCBasedType, metaclass=ABCMeta):
    _regexp: CachedValue[tuple[NERCRegexp, ...]] = field(default_factory=CachedValue)
    _black_regexp: CachedValue[tuple[NERCRegexp, ...]] = field(default_factory=CachedValue)
    _pretrained_nerc_models: CachedValue[tuple[str, ...]] = field(default_factory=CachedValue)
    _dictionary: CachedValue[tuple[str, ...]] = field(default_factory=CachedValue)
    _black_list: CachedValue[tuple[str, ...]] = field(default_factory=CachedValue)

    def __post_init__(self):
        AbstractAdapterBasedType.__post_init__(self)
        AbstractNERCBasedType.__post_init__(self)
        if any(not isinstance(getattr(self, field), CachedValue) for field in [
            '_regexp', '_black_regexp', '_pretrained_nerc_models', '_dictionary', '_black_list'
        ]):
            raise ValueError

    @property
    @cached
    async def regexp(self) -> tuple[NERCRegexp, ...]:
        type_ = await self._load_object(regexp=True)
        return tuple(NERCRegexp(**data) for data in type_['regexp'])

    @property
    @cached
    async def black_regexp(self) -> tuple[NERCRegexp, ...]:
        type_ = await self._load_object(black_regexp=True)
        return tuple(NERCRegexp(**data) for data in type_['black_regexp'])

    @property
    @cached
    async def pretrained_nerc_models(self) -> tuple[str, ...]:
        type_ = await self._load_object(pretrained_models=True)
        return tuple(type_['pretrained_models'])

    @property
    @cached
    async def dictionary(self) -> tuple[str, ...]:
        type_ = await self._load_object(dictionary=True)
        return tuple(chain(type_.get('dictionary', ()), type_.get('names_dictionary', ())))

    @property
    @cached
    async def black_list(self) -> tuple[str, ...]:
        type_ = await self._load_object(black_list=True)
        return tuple(type_['black_list'])

    @abstractmethod
    async def _load_object(
            self,
            regexp: bool = False,
            black_regexp: bool = False,
            pretrained_models: bool = False,
            dictionary: bool = False,
            black_list: bool = False
    ):
        pass

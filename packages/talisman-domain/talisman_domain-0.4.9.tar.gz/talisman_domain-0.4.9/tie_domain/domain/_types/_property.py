from dataclasses import dataclass

from tp_interfaces.domain.abstract import AbstractIdentifyingPropertyType, AbstractPropertyType, AbstractRelationPropertyType
from ._nerc import NERCBasedType
from ._relext import RelExtBasedType


@dataclass(frozen=True)
class PropertyType(RelExtBasedType, AbstractPropertyType):
    def __post_init__(self):
        RelExtBasedType.__post_init__(self)
        AbstractPropertyType.__post_init__(self)

    async def _load_object(self) -> dict:
        return await self._api.property_type_extras(self)


@dataclass(frozen=True)
class IdentifyingPropertyType(NERCBasedType, AbstractIdentifyingPropertyType):

    def __post_init__(self):
        NERCBasedType.__post_init__(self)
        AbstractIdentifyingPropertyType.__post_init__(self)

    async def _load_object(
            self,
            regexp: bool = False,
            black_regexp: bool = False,
            pretrained_models: bool = False,
            dictionary: bool = False,
            black_list: bool = False
    ):
        return await self._api.id_property_type_extras(self, regexp, black_regexp, pretrained_models, dictionary, black_list)


@dataclass(frozen=True)
class RelationPropertyType(RelExtBasedType, AbstractRelationPropertyType):

    def __post_init__(self):
        RelExtBasedType.__post_init__(self)
        AbstractPropertyType.__post_init__(self)

    async def _load_object(self) -> dict:
        return await self._api.relation_property_type_extras(self)

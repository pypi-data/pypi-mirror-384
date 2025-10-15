from abc import abstractmethod
from typing import AsyncIterator

from talisman_api import AbstractTalismanAPI
from tp_interfaces.domain.abstract import AbstractIdentifyingPropertyType, AbstractLiteralValueType, AbstractPropertyType, \
    AbstractRelationPropertyType, AbstractRelationType


class TalismanDomainAPI(AbstractTalismanAPI):

    @abstractmethod
    async def concept_types(self) -> AsyncIterator[dict]:
        pass

    @abstractmethod
    async def document_types(self) -> AsyncIterator[dict]:
        pass

    @abstractmethod
    async def literal_value_types(self) -> AsyncIterator[dict]:
        pass

    @abstractmethod
    async def composite_value_types(self) -> AsyncIterator[dict]:
        pass

    @abstractmethod
    async def relation_types(self) -> AsyncIterator[dict]:
        pass

    @abstractmethod
    async def property_types(self) -> AsyncIterator[dict]:
        pass

    @abstractmethod
    async def relation_property_types(self) -> AsyncIterator[dict]:
        pass

    @abstractmethod
    async def property_type_extras(self, prop_type: AbstractPropertyType) -> dict:
        pass

    @abstractmethod
    async def relation_property_type_extras(self, rel_prop_type: AbstractRelationPropertyType) -> dict:
        pass

    @abstractmethod
    async def relation_type_extras(self, rel_type: AbstractRelationType) -> dict:
        pass

    @abstractmethod
    async def id_property_type_extras(
            self,
            prop_type: AbstractIdentifyingPropertyType,
            regexp: bool = False,
            black_regexp: bool = False,
            pretrained_models: bool = False,
            dictionary: bool = False,
            black_list: bool = False
    ) -> dict:
        pass

    @abstractmethod
    async def literal_value_type_extras(
            self,
            value_type: AbstractLiteralValueType,
            regexp: bool = False,
            black_regexp: bool = False,
            pretrained_models: bool = False,
            dictionary: bool = False,
            black_list: bool = False
    ) -> dict:
        pass

    @abstractmethod
    async def domain_update_info(self) -> set[tuple[str, int]]:
        pass

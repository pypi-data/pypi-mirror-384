from dataclasses import dataclass

from tp_interfaces.domain.abstract import AbstractRelationType
from ._relext import RelExtBasedType


@dataclass(frozen=True)
class RelationType(RelExtBasedType, AbstractRelationType):
    def __post_init__(self):
        RelExtBasedType.__post_init__(self)
        AbstractRelationType.__post_init__(self)

    async def _load_object(self) -> dict:
        return await self._api.relation_type_extras(self)

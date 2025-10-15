from dataclasses import dataclass

from tp_interfaces.domain.abstract import AbstractComponentValueType
from ._relext import RelExtBasedType


@dataclass(frozen=True)
class ComponentValueType(RelExtBasedType, AbstractComponentValueType):

    async def _load_object(self) -> dict:
        raise NotImplementedError

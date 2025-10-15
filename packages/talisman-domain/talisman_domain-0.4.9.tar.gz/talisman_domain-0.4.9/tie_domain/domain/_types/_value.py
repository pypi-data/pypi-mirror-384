from dataclasses import dataclass

from tp_interfaces.domain.abstract import AbstractLiteralValueType
from ._nerc import NERCBasedType


@dataclass(frozen=True)
class AtomValueType(NERCBasedType, AbstractLiteralValueType):
    def __post_init__(self):
        NERCBasedType.__post_init__(self)
        AbstractLiteralValueType.__post_init__(self)

    async def _load_object(
            self,
            regexp: bool = False,
            black_regexp: bool = False,
            pretrained_models: bool = False,
            dictionary: bool = False,
            black_list: bool = False
    ):
        return await self._api.literal_value_type_extras(self, regexp, black_regexp, pretrained_models, dictionary, black_list)

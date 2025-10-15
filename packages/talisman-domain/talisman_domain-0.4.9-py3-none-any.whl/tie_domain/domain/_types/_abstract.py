from abc import ABCMeta
from dataclasses import dataclass

from tdm.abstract.datamodel import AbstractDomainType

from tie_domain.domain.api import TalismanDomainAPI


@dataclass(frozen=True)
class AbstractAdapterBasedType(AbstractDomainType, metaclass=ABCMeta):
    _api: TalismanDomainAPI = None

    def __post_init__(self):
        if self._api is None:
            raise ValueError

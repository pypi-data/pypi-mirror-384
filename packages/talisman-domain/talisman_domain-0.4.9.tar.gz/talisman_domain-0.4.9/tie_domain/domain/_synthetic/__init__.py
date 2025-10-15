__all__ = [
    'generate_types'
]

from itertools import chain
from typing import Iterable

from tdm.abstract.datamodel import AbstractDomainType
from tdm.datamodel.domain import Domain

from ._category import generate_types as generate_category_types
from ._platform import generate_types as generate_platform_types


def generate_types(domain: Domain) -> Iterable[AbstractDomainType]:
    return chain(
        generate_platform_types(domain),
        generate_category_types(domain)
    )

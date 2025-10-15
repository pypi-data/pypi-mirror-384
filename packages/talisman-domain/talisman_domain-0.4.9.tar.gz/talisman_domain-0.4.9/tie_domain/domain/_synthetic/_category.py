from typing import Iterable

from tdm.abstract.datamodel import AbstractDomainType
from tdm.datamodel.domain import ConceptType, Domain

from tp_interfaces.domain.model.types import IdentifyingPropertyType, PropertyType
from ._common import STR_VALUE

# CONCEPTS
RUBRIC = ConceptType('Рубрика', id='rubric')

# PROPERTIES
RUBRIC_ID = IdentifyingPropertyType("Название", RUBRIC, STR_VALUE, id='rubric_id')
RUBRICATOR_ID = PropertyType("Рубрикатор", RUBRIC, STR_VALUE, id='rubricator_id')


def generate_types(domain: Domain) -> Iterable[AbstractDomainType]:
    return RUBRIC, RUBRIC_ID, RUBRICATOR_ID

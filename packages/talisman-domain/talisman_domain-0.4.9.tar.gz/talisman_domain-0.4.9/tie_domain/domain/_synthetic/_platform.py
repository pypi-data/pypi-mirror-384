from typing import Iterable

from tdm.abstract.datamodel import AbstractDomainType
from tdm.datamodel.domain import AccountType, Domain, PlatformType
from tdm.datamodel.values import StringValue

from tp_interfaces.domain.model.types import AtomValueType, IdentifyingPropertyType, PropertyType, RelationType
from ._common import STR_VALUE

_PLATFORM_TYPE_ENUM = (
    'government',
    'fileStorage',
    'database',
    'procurement',
    'review',
    'forum',
    'newsAggregator',
    'media',
    'blog',
    'messenger',
    'socialNetwork'
)

# VALUES

PLATFORM_VALUE = AtomValueType("platform_value", StringValue, id='platform_value', value_restriction=_PLATFORM_TYPE_ENUM)

# CONCEPTS
PLATFORM = PlatformType('platform', id='platform')
ACCOUNT = AccountType('account', id='account')

# RELATIONS
ACCOUNT_PLATFORM = RelationType("account_platform", ACCOUNT, PLATFORM, id="account_platform")

# PROPERTIES
ACCOUNT_KEY = IdentifyingPropertyType("Название", ACCOUNT, STR_VALUE, id="account_key")
ACCOUNT_NAME = PropertyType("account_name", ACCOUNT, STR_VALUE, id="account_name")
ACCOUNT_URL = PropertyType("account_url", ACCOUNT, STR_VALUE, id="account_url")

PLATFORM_KEY = IdentifyingPropertyType("Название", PLATFORM, STR_VALUE, id="platform_key")
PLATFORM_NAME = PropertyType("platform_name", PLATFORM, STR_VALUE, id="platform_name")
PLATFORM_URL = PropertyType("platform_url", PLATFORM, STR_VALUE, id="platform_url")
PLATFORM_TYPE = PropertyType("platform_type", PLATFORM, PLATFORM_VALUE, id="platform_type")

TYPES = (
    PLATFORM_VALUE, STR_VALUE,
    PLATFORM, ACCOUNT,
    ACCOUNT_PLATFORM,
    ACCOUNT_KEY, ACCOUNT_NAME, ACCOUNT_URL,
    PLATFORM_KEY, PLATFORM_NAME, PLATFORM_URL, PLATFORM_TYPE
)


def generate_types(domain: Domain) -> Iterable[AbstractDomainType]:
    return TYPES

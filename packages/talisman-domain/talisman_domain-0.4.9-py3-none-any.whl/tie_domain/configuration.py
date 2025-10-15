from typing import Type

from tp_interfaces.domain.interfaces import DomainProducer


def _get_domain() -> Type[DomainProducer]:
    from tie_domain.domain.producer import TalismanDomainProducer
    return TalismanDomainProducer


DOMAIN_FACTORY = _get_domain

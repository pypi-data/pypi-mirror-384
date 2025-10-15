from typing import Type

from tp_interfaces.abstract import ModelTypeFactory
from ._abstract import AbstractDomainUpdatesManager


def _never() -> Type[AbstractDomainUpdatesManager]:
    from ._never import NeverDomainUpdatesManager
    return NeverDomainUpdatesManager


def _timeout() -> Type[AbstractDomainUpdatesManager]:
    from ._timeout import TimeoutDomainUpdatesManager
    return TimeoutDomainUpdatesManager


def _ask_kb() -> Type[AbstractDomainUpdatesManager]:
    from ._ask import AskKBDomainUpdatesManager
    return AskKBDomainUpdatesManager


MANAGERS = ModelTypeFactory({
    'never': _never,
    'timeout': _timeout,
    'ask kb': _ask_kb
})

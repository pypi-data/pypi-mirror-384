import asyncio
from functools import wraps
from typing import Generic, TypeVar

T = TypeVar('T')


class CachedValue(Generic[T]):
    def __init__(self, value: T = None):
        self._value = value

    @property
    def empty(self) -> bool:
        return self._value is None

    @property
    def value(self) -> T:
        if self._value is None:
            raise AttributeError
        return self._value

    @value.setter
    def value(self, value: T) -> None:
        if self._value is not None:
            raise AttributeError
        self._value = value


def cached(f):
    name = f"_{f.__name__}"

    lock = asyncio.Lock()

    @wraps(f)
    async def eval_if_needed(self):
        attr = getattr(self, name)
        if not isinstance(attr, CachedValue):
            raise ValueError
        if not attr.empty:
            return attr.value
        async with lock:
            if not attr.empty:  # we should check it once again to guarantee single execution
                return attr.value
            attr.value = await f(self)
        return attr.value

    return eval_if_needed

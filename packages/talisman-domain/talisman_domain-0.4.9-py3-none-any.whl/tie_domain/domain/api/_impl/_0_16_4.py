from typing import AsyncIterator

from talisman_api import APISchema, version
from ._abstract import TalismanDomainAPIImpl


@version('0.16.4')
class _ImplV164(TalismanDomainAPIImpl):
    async def property_types(self) -> AsyncIterator[dict]:
        for property_parent in ['concept', 'document']:
            async for i in self._client(APISchema.KB_UTILS).paginate_items(
                    operation_name='paginationPropertyTypeIE',
                    variables={'property_parent': property_parent}
            ):
                yield i

    async def relation_property_types(self) -> AsyncIterator[dict]:
        async for i in self._client(APISchema.KB_UTILS).paginate_items(
                operation_name='paginationPropertyTypeIE',
                variables={'property_parent': 'conceptLink'}
        ):
            yield i

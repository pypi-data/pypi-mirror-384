from typing_extensions import Self

from talisman_api.api_client import APISchema, CompositeTalismanAPIClient
from talisman_api.api_client.composite import GQLClientConfig
from tie_domain.domain.api import TalismanDomainAPI
from ._abstract import AbstractDomainUpdatesManager


class AskKBDomainUpdatesManager(AbstractDomainUpdatesManager):
    def __init__(self, client: CompositeTalismanAPIClient):
        self._client = client
        self._api: TalismanDomainAPI | None = None

        self._timestamps: set[tuple] = set()

    async def __aenter__(self) -> Self:
        self._api = await TalismanDomainAPI.get_compatible_api(self._client)
        self._timestamps = await self._get_timestamps()
        return self

    async def __aexit__(self, __exc_type, __exc_value, __traceback):
        self._timestamps = set()
        self._api = None

    async def _get_timestamps(self) -> set[tuple]:
        return await self._api.domain_update_info()

    @property
    async def has_changed(self) -> bool:
        new_timestamps = await self._get_timestamps()
        return self._timestamps != new_timestamps

    async def update(self) -> None:
        self._timestamps = await self._get_timestamps()

    @classmethod
    def from_config(cls, config: dict) -> Self:
        return cls(CompositeTalismanAPIClient({APISchema(name): GQLClientConfig(**cfg) for name, cfg in config['client'].items()}))

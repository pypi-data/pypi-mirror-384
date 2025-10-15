import logging
import os
from typing import Iterable, TypeVar

from tdm.abstract.datamodel import AbstractDomainType
from tdm.datamodel.domain import CompositeValueType, ConceptType, DocumentType, Domain

from talisman_api.api_client import APISchema, CompositeTalismanAPIClient
from talisman_api.api_client.client import GQLClientConfig
from tp_interfaces.domain.hooks import DOMAIN_CHANGE_HOOKS
from tp_interfaces.domain.interfaces import AbstractDomainChangeHook, DomainProducer
from tp_interfaces.domain.value import ValueTypes
from tp_interfaces.logging.time import log_time
from ._types import AtomValueType, ComponentValueType, IdentifyingPropertyType, PropertyType, RelationPropertyType, RelationType
from .api import TalismanDomainAPI
from .updates_manager import AbstractDomainUpdatesManager, MANAGERS

logger = logging.getLogger(__name__)

_SYNTHETIC_TYPES = bool(os.getenv('SYNTHETIC_TYPES', True))

_T = TypeVar('_T', bound=AbstractDomainType)


class TalismanDomainProducer(DomainProducer):
    def __init__(
            self, client: CompositeTalismanAPIClient, updates_manager: AbstractDomainUpdatesManager,
            hooks: Iterable[AbstractDomainChangeHook] = tuple()
    ):
        super().__init__(hooks)
        self._client = client
        self._api: TalismanDomainAPI | None = None
        self._updates_manager = updates_manager

    async def __aenter__(self):
        self._api = await TalismanDomainAPI.get_compatible_api(self._client)
        await self._updates_manager.__aenter__()
        return self

    async def __aexit__(self, *exc):
        await self._updates_manager.__aexit__(*exc)
        self._api = None

    @log_time(logger=logger)
    async def has_changed(self) -> bool:
        return await self._updates_manager.has_changed

    @log_time(logger=logger)
    async def _get_domain(self) -> Domain:  # noqa: C901
        await self._updates_manager.update()  # first we notify manager, that we reload domain

        types: dict[str, AbstractDomainType] = {}

        async for concept in self._api.concept_types():
            types[concept['id']] = ConceptType(name=concept['name'], id=concept['id'])

        async for document in self._api.document_types():
            types[document['id']] = DocumentType(name=document['name'], id=document['id'])

        async for value in self._api.literal_value_types():
            types[value['id']] = AtomValueType(
                name=value['name'],
                value_type=ValueTypes.get(value['valueType'], value['valueType']),
                id=value['id'],
                value_restriction=tuple(value['valueRestriction']),
                _api=self._api
            )

        async for composite in self._api.composite_value_types():
            c = CompositeValueType(name=composite['name'], id=composite['id'])
            types[c.id] = c

            for component in composite['componentValueTypes']:
                types[component['id']] = ComponentValueType(
                    name=component['name'],
                    source=c,
                    target=types[component['valueType']['id']],
                    id=component['id'],
                    isRequired=component['isRequired'],
                    _api=self._api
                )
        async for relation in self._api.relation_types():
            try:
                types[relation['id']] = RelationType(
                    name=relation['name'],
                    source=types[relation['source']['id']],
                    target=types[relation['target']['id']],
                    id=relation['id'],
                    directed=relation['isDirected'],
                    _api=self._api
                )
            except KeyError as e:  # TODO: remove it after account/platform support
                log_error(relation, types, e)
                continue
        async for prop in self._api.property_types():
            try:
                if prop['isIdentifying']:
                    types[prop['id']] = IdentifyingPropertyType(
                        name=prop['name'],
                        source=types[prop['source']['id']],
                        target=types[prop['target']['id']],
                        id=prop['id'],
                        _api=self._api
                    )
                else:
                    types[prop['id']] = PropertyType(
                        name=prop['name'],
                        source=types[prop['source']['id']],
                        target=types[prop['target']['id']],
                        id=prop['id'],
                        _api=self._api
                    )
            except KeyError as e:  # TODO: remove it after account/platform support
                log_error(prop, types, e)
                continue
        async for prop in self._api.relation_property_types():
            try:
                types[prop['id']] = RelationPropertyType(
                    name=prop['name'],
                    source=types[prop['source']['id']],
                    target=types[prop['target']['id']],
                    id=prop['id'],
                    _api=self._api
                )
            except KeyError as e:  # TODO: remove it after account/platform support
                log_error(prop, types, e)
                continue
        final_types = set(types.values())

        if _SYNTHETIC_TYPES:
            from ._synthetic import generate_types
            final_types.update(generate_types(Domain(final_types)))
        return Domain(final_types)

    @classmethod
    def from_config(cls, config: dict) -> 'TalismanDomainProducer':
        hooks = []
        for hook_cfg in config.get('hooks', []):
            if isinstance(hook_cfg, str):
                name, cfg = hook_cfg, {}
            elif isinstance(hook_cfg, dict):
                name, cfg = hook_cfg['name'], hook_cfg.get('config', {})
            else:
                raise ValueError
            hooks.append(DOMAIN_CHANGE_HOOKS[name].from_config(cfg))
        updates_cfg = config.get('updates', {})
        updates_manager = MANAGERS[updates_cfg.get('strategy', 'never')].from_config(updates_cfg.get('config', {}))
        client = CompositeTalismanAPIClient({APISchema(name): GQLClientConfig(**cfg) for name, cfg in config['adapter'].items()})
        return cls(client, updates_manager, hooks)


def log_error(type_: dict, types: dict[str, AbstractDomainType], exception: Exception) -> None:
    reasons = []
    if type_['source']['id'] not in types:
        reasons.append(f"\n- unknown source domain type [{type_['source']['id']}]")
    if type_['target']['id'] not in types:
        reasons.append(f"\n- unknown target domain type [{type_['target']['id']}]")
    logger.warning(
        f"Relation type [{type_['id']}]({type_['name']}) is ignored because of following reasons:{''.join(reasons)}",
        extra={'type': str(type_)},
        exc_info=exception
    )

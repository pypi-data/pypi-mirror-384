from typing import Iterable, List, Union

from benchling_api_client.v2.stable.api.registry import (
    bulk_get_registered_entities,
    get_registry,
    list_registries,
    register_entities,
    unregister_entities,
)
from benchling_api_client.v2.stable.extensions import UnknownType

from benchling_sdk.helpers.decorators import api_method
from benchling_sdk.helpers.logging_helpers import check_for_csv_bug_fix
from benchling_sdk.helpers.response_helpers import model_from_detailed
from benchling_sdk.helpers.serialization_helpers import array_query_param
from benchling_sdk.helpers.task_helpers import EmptyTaskResponse, TaskHelper
from benchling_sdk.models import (
    AaSequenceWithEntityType,
    CustomEntityWithEntityType,
    DnaOligoWithEntityType,
    DnaSequenceWithEntityType,
    MixtureWithEntityType,
    NamingStrategy,
    RegisterEntities,
    Registry,
    RnaOligoWithEntityType,
    UnregisterEntities,
)
from benchling_sdk.services.v2.base_service import BaseService

TypedEntity = Union[
    CustomEntityWithEntityType,
    DnaSequenceWithEntityType,
    AaSequenceWithEntityType,
    MixtureWithEntityType,
    DnaOligoWithEntityType,
    RnaOligoWithEntityType,
    UnknownType,
]


class RegistryService(BaseService):
    """
    Registry.

    Manage registry objects.

    See https://benchling.com/api/reference#/Registry
    """

    @api_method
    def register(
        self,
        registry_id: str,
        entity_ids: Iterable[str],
        naming_strategy: NamingStrategy = NamingStrategy.NEW_IDS,
    ) -> TaskHelper[EmptyTaskResponse]:
        """
        Register entities.

        Attempts to move entities into the registry. This endpoint will first check that the entities
        are all valid to be moved into the registry, given the namingStrategy. If any entities fail validation,
        no files will be moved and errors describing invalid entities is returned.

        If all entities pass validation, the entities are moved into the registry.

        See https://benchling.com/api/reference#/Registry/registerEntities
        """
        registration_body = RegisterEntities(entity_ids=list(entity_ids), naming_strategy=naming_strategy)
        response = register_entities.sync_detailed(
            client=self.client, registry_id=registry_id, json_body=registration_body
        )
        return self._task_helper_from_response(response, EmptyTaskResponse)

    @api_method
    def unregister(
        self,
        registry_id: str,
        entity_ids: Iterable[str],
        folder_id: str,
    ) -> None:
        """
        Unregister entities.

        Unregisters entities and moves them to a folder.

        See https://benchling.com/api/reference#/Registry/unregisterEntities
        """
        registration_body = UnregisterEntities(entity_ids=list(entity_ids), folder_id=folder_id)
        response = unregister_entities.sync_detailed(
            client=self.client, registry_id=registry_id, json_body=registration_body
        )
        # Raise for error but return nothing
        model_from_detailed(response)

    @api_method
    def registries(self) -> List[Registry]:
        """
        List registries.

        See https://benchling.com/api/reference#/Registry/listRegistries

        :return: A list of registries
        :rtype: List[Registry]
        """
        response = list_registries.sync_detailed(client=self.client)
        registry_list = model_from_detailed(response)
        if not registry_list.registries:
            return []
        return registry_list.registries

    # TODO Currently this payload does not deserialize properly until
    # https://github.com/triaxtec/openapi-python-client/issues/219

    @api_method
    def entities(self, registry_id: str, entity_registry_ids: Iterable[str]) -> List[TypedEntity]:
        """
        Bulk get registered entities.

        See https://benchling.com/api/reference#/Registry/bulkGetRegisteredEntities
        """
        check_for_csv_bug_fix("entity_registry_ids", entity_registry_ids)

        response = bulk_get_registered_entities.sync_detailed(
            client=self.client,
            registry_id=registry_id,
            entity_registry_ids=array_query_param(entity_registry_ids),
        )
        entity_list = model_from_detailed(response)
        if not entity_list.entities:
            return []
        return entity_list.entities

    @api_method
    def get_by_id(self, registry_id: str) -> Registry:
        """
        Get registry.

        See https://benchling.com/api/reference#/Registry/getRegistry
        """
        response = get_registry.sync_detailed(client=self.client, registry_id=registry_id)
        return model_from_detailed(response)

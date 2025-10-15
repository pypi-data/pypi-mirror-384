from typing import Any, Dict, Iterable, List, Optional, Union

from benchling_api_client.v2.stable.api.dna_oligos import (
    archive_dna_oligos,
    bulk_create_dna_oligos,
    bulk_update_dna_oligos,
    bulk_upsert_dna_oligos,
    create_dna_oligo,
    get_dna_oligo,
    list_dna_oligos,
    unarchive_dna_oligos,
    update_dna_oligo,
    upsert_dna_oligo,
)
from benchling_api_client.v2.types import Response

from benchling_sdk.errors import raise_for_status
from benchling_sdk.helpers.constants import _translate_to_string_enum
from benchling_sdk.helpers.decorators import api_method
from benchling_sdk.helpers.pagination_helpers import NextToken, PageIterator
from benchling_sdk.helpers.response_helpers import model_from_detailed
from benchling_sdk.helpers.serialization_helpers import (
    none_as_unset,
    optional_array_query_param,
    schema_fields_query_param,
)
from benchling_sdk.helpers.task_helpers import TaskHelper
from benchling_sdk.models import (
    BulkCreateDnaOligosAsyncTaskResponse,
    BulkUpdateDnaOligosAsyncTaskResponse,
    DnaOligo,
    DnaOligoBulkUpdate,
    DnaOligoCreate,
    DnaOligosArchivalChange,
    DnaOligosArchive,
    DnaOligosBulkCreateRequest,
    DnaOligosBulkUpdateRequest,
    DnaOligosBulkUpsertRequest,
    DnaOligosPaginatedList,
    DnaOligosUnarchive,
    DnaOligoUpdate,
    EntityArchiveReason,
    ListDNAOligosSort,
    OligoUpsertRequest,
)
from benchling_sdk.services.v2.base_service import BaseService


class DnaOligoService(BaseService):
    """
    DNA Oligos.

    DNA Oligos are short linear DNA sequences that can be attached as primers to full DNA sequences. Just like other
    entities, they support schemas, tags, and aliases.
    See https://benchling.com/api/reference#/DNA%20Oligos
    """

    @api_method
    def get_by_id(self, oligo_id: str, custom_notation_id: Optional[str] = None) -> DnaOligo:
        """
        Get a DNA Oligo by ID.

        See https://benchling.com/api/reference#/DNA%20Oligos/getDNAOligo
        """
        response = get_dna_oligo.sync_detailed(
            client=self.client, oligo_id=oligo_id, custom_notation_id=none_as_unset(custom_notation_id)
        )
        return model_from_detailed(response)

    @api_method
    def _dna_oligos_page(
        self,
        modified_at: Optional[str] = None,
        created_at: Optional[str] = None,
        name: Optional[str] = None,
        bases: Optional[str] = None,
        folder_id: Optional[str] = None,
        mentioned_in: Optional[List[str]] = None,
        project_id: Optional[str] = None,
        registry_id: Optional[str] = None,
        schema_id: Optional[str] = None,
        archive_reason: Optional[str] = None,
        mentions: Optional[List[str]] = None,
        sort: Optional[ListDNAOligosSort] = None,
        ids: Optional[Iterable[str]] = None,
        entity_registry_ids_any_of: Optional[Iterable[str]] = None,
        name_includes: Optional[str] = None,
        names_any_of: Optional[Iterable[str]] = None,
        names_any_of_case_sensitive: Optional[Iterable[str]] = None,
        schema_fields: Optional[Dict[str, Any]] = None,
        creator_ids: Optional[Iterable[str]] = None,
        page_size: Optional[int] = None,
        next_token: Optional[NextToken] = None,
        author_idsany_of: Optional[Iterable[str]] = None,
        returning: Optional[Iterable[str]] = None,
        custom_notation_id: Optional[str] = None,
    ) -> Response[DnaOligosPaginatedList]:
        response = list_dna_oligos.sync_detailed(
            client=self.client,
            modified_at=none_as_unset(modified_at),
            created_at=none_as_unset(created_at),
            name=none_as_unset(name),
            bases=none_as_unset(bases),
            folder_id=none_as_unset(folder_id),
            mentioned_in=none_as_unset(optional_array_query_param(mentioned_in)),
            project_id=none_as_unset(project_id),
            registry_id=none_as_unset(registry_id),
            schema_id=none_as_unset(schema_id),
            archive_reason=none_as_unset(archive_reason),
            mentions=none_as_unset(optional_array_query_param(mentions)),
            sort=none_as_unset(sort),
            ids=none_as_unset(optional_array_query_param(ids)),
            entity_registry_idsany_of=none_as_unset(optional_array_query_param(entity_registry_ids_any_of)),
            name_includes=none_as_unset(name_includes),
            namesany_of=none_as_unset(optional_array_query_param(names_any_of)),
            namesany_ofcase_sensitive=none_as_unset(optional_array_query_param(names_any_of_case_sensitive)),
            schema_fields=none_as_unset(schema_fields_query_param(schema_fields)),
            creator_ids=none_as_unset(optional_array_query_param(creator_ids)),
            page_size=none_as_unset(page_size),
            next_token=none_as_unset(next_token),
            author_idsany_of=none_as_unset(optional_array_query_param(author_idsany_of)),
            returning=none_as_unset(optional_array_query_param(returning)),
            custom_notation_id=none_as_unset(custom_notation_id),
        )
        raise_for_status(response)
        return response  # type: ignore

    def list(
        self,
        modified_at: Optional[str] = None,
        created_at: Optional[str] = None,
        name: Optional[str] = None,
        bases: Optional[str] = None,
        folder_id: Optional[str] = None,
        mentioned_in: Optional[List[str]] = None,
        project_id: Optional[str] = None,
        registry_id: Optional[str] = None,
        schema_id: Optional[str] = None,
        archive_reason: Optional[str] = None,
        mentions: Optional[List[str]] = None,
        ids: Optional[Iterable[str]] = None,
        entity_registry_ids_any_of: Optional[Iterable[str]] = None,
        name_includes: Optional[str] = None,
        names_any_of: Optional[Iterable[str]] = None,
        names_any_of_case_sensitive: Optional[Iterable[str]] = None,
        schema_fields: Optional[Dict[str, Any]] = None,
        creator_ids: Optional[Iterable[str]] = None,
        sort: Optional[Union[str, ListDNAOligosSort]] = None,
        page_size: Optional[int] = None,
        author_idsany_of: Optional[Iterable[str]] = None,
        returning: Optional[Iterable[str]] = None,
        custom_notation_id: Optional[str] = None,
    ) -> PageIterator[DnaOligo]:
        """
        List DNA Oligos.

        See https://benchling.com/api/reference#/DNA%20Oligos/listDNAOligos
        """

        def api_call(next_token: NextToken) -> Response[DnaOligosPaginatedList]:
            return self._dna_oligos_page(
                modified_at=modified_at,
                created_at=created_at,
                name=name,
                bases=bases,
                folder_id=folder_id,
                mentioned_in=mentioned_in,
                project_id=project_id,
                registry_id=registry_id,
                schema_id=schema_id,
                archive_reason=archive_reason,
                mentions=mentions,
                ids=ids,
                entity_registry_ids_any_of=entity_registry_ids_any_of,
                name_includes=name_includes,
                names_any_of=names_any_of,
                names_any_of_case_sensitive=names_any_of_case_sensitive,
                schema_fields=schema_fields,
                creator_ids=creator_ids,
                sort=_translate_to_string_enum(ListDNAOligosSort, sort),
                page_size=page_size,
                next_token=next_token,
                author_idsany_of=author_idsany_of,
                returning=returning,
                custom_notation_id=custom_notation_id,
            )

        def results_extractor(body: DnaOligosPaginatedList) -> Optional[List[DnaOligo]]:
            return body.dna_oligos

        return PageIterator(api_call, results_extractor)

    @api_method
    def create(self, dna_oligo: DnaOligoCreate) -> DnaOligo:
        """
        Create a DNA Oligo.

        See https://benchling.com/api/reference#/DNA%20Oligos/createDNAOligo
        """
        response = create_dna_oligo.sync_detailed(client=self.client, json_body=dna_oligo)
        return model_from_detailed(response)

    @api_method
    def update(self, oligo_id: str, dna_oligo: DnaOligoUpdate) -> DnaOligo:
        """
        Update a DNA Oligo.

        See https://benchling.com/api/reference#/DNA%20Oligos/updateDNAOligo
        """
        response = update_dna_oligo.sync_detailed(client=self.client, oligo_id=oligo_id, json_body=dna_oligo)
        return model_from_detailed(response)

    @api_method
    def archive(self, dna_oligo_ids: Iterable[str], reason: EntityArchiveReason) -> DnaOligosArchivalChange:
        """
        Archive DNA Oligos.

        See https://benchling.com/api/reference#/DNA%20Oligos/archiveDNAOligos
        """
        archive_request = DnaOligosArchive(reason=reason, dna_oligo_ids=list(dna_oligo_ids))
        response = archive_dna_oligos.sync_detailed(client=self.client, json_body=archive_request)
        return model_from_detailed(response)

    @api_method
    def unarchive(self, dna_oligo_ids: Iterable[str]) -> DnaOligosArchivalChange:
        """
        Unarchive DNA Oligos.

        See https://benchling.com/api/reference#/DNA%20Oligos/unarchiveDNAOligos
        """
        unarchive_request = DnaOligosUnarchive(dna_oligo_ids=list(dna_oligo_ids))
        response = unarchive_dna_oligos.sync_detailed(client=self.client, json_body=unarchive_request)
        return model_from_detailed(response)

    @api_method
    def bulk_create(
        self, dna_oligos: Iterable[DnaOligoCreate]
    ) -> TaskHelper[BulkCreateDnaOligosAsyncTaskResponse]:
        """
        Bulk create DNA Oligos.

        See https://benchling.com/api/reference#/DNA%20Oligos/bulkCreateDNAOligos
        """
        body = DnaOligosBulkCreateRequest(list(dna_oligos))
        response = bulk_create_dna_oligos.sync_detailed(client=self.client, json_body=body)
        return self._task_helper_from_response(response, BulkCreateDnaOligosAsyncTaskResponse)

    @api_method
    def bulk_update(
        self, dna_oligos: Iterable[DnaOligoBulkUpdate]
    ) -> TaskHelper[BulkUpdateDnaOligosAsyncTaskResponse]:
        """
        Bulk update DNA oligos.

        See https://benchling.com/api/reference#/DNA%20Oligos/bulkUpdateDNAOligos
        """
        body = DnaOligosBulkUpdateRequest(list(dna_oligos))
        response = bulk_update_dna_oligos.sync_detailed(client=self.client, json_body=body)
        return self._task_helper_from_response(response, BulkUpdateDnaOligosAsyncTaskResponse)

    @api_method
    def upsert(self, entity_registry_id: str, dna_oligo: OligoUpsertRequest) -> DnaOligo:
        """
        Create or modify a DNA Oligo.

        See https://benchling.com/api/reference#/DNA%20Oligos/upsertDNAOligo
        """
        response = upsert_dna_oligo.sync_detailed(
            client=self.client, entity_registry_id=entity_registry_id, json_body=dna_oligo
        )
        return model_from_detailed(response)

    @api_method
    def bulk_upsert(
        self, body: DnaOligosBulkUpsertRequest, returning: Optional[Iterable[str]] = None
    ) -> TaskHelper[BulkUpdateDnaOligosAsyncTaskResponse]:
        """
        Bulk create or update DNA Oligos.

        See https://benchling.com/api/reference#/DNA%20Oligos/bulkUpsertDnaOligos
        """
        returning_string = optional_array_query_param(returning)
        response = bulk_upsert_dna_oligos.sync_detailed(
            client=self.client, json_body=body, returning=none_as_unset(returning_string)
        )
        return self._task_helper_from_response(response, BulkUpdateDnaOligosAsyncTaskResponse)

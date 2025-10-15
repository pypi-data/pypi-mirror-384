from typing import Any, Dict, Iterable, List, Optional, Union

from benchling_api_client.v2.stable.api.dna_sequences import (
    archive_dna_sequences,
    auto_annotate_dna_sequences,
    autofill_dna_sequence_parts,
    autofill_dna_sequence_transcriptions,
    autofill_dna_sequence_translations,
    bulk_create_dna_sequences,
    bulk_get_dna_sequences,
    bulk_update_dna_sequences,
    bulk_upsert_dna_sequences,
    create_dna_sequence,
    find_matching_regions_dna_sequences,
    get_dna_sequence,
    list_dna_sequences,
    match_bases_dna_sequences,
    optimize_codons,
    search_dna_sequences,
    unarchive_dna_sequences,
    update_dna_sequence,
    upsert_dna_sequence,
)
from benchling_api_client.v2.types import Response

from benchling_sdk.errors import raise_for_status
from benchling_sdk.helpers.constants import _translate_to_string_enum
from benchling_sdk.helpers.decorators import api_method
from benchling_sdk.helpers.logging_helpers import check_for_csv_bug_fix
from benchling_sdk.helpers.pagination_helpers import NextToken, PageIterator
from benchling_sdk.helpers.response_helpers import model_from_detailed
from benchling_sdk.helpers.serialization_helpers import (
    none_as_unset,
    optional_array_query_param,
    schema_fields_query_param,
)
from benchling_sdk.helpers.task_helpers import EmptyTaskResponse, TaskHelper
from benchling_sdk.models import (
    AutoAnnotateDnaSequences,
    AutofillSequences,
    BulkCreateDnaSequencesAsyncTaskResponse,
    BulkUpdateDnaSequencesAsyncTaskResponse,
    DnaSequence,
    DnaSequenceBulkCreate,
    DnaSequenceBulkUpdate,
    DnaSequenceCreate,
    DnaSequencesArchivalChange,
    DnaSequencesArchive,
    DnaSequencesBulkCreateRequest,
    DnaSequencesBulkUpdateRequest,
    DnaSequencesBulkUpsertRequest,
    DnaSequencesFindMatchingRegion,
    DnaSequencesPaginatedList,
    DnaSequencesUnarchive,
    DnaSequenceUpdate,
    DnaSequenceUpsertRequest,
    EntityArchiveReason,
    FindMatchingRegionsDnaAsyncTaskResponse,
    ListDNASequencesSort,
    MatchBasesRequest,
    OptimizeCodons,
    SearchBasesRequest,
)
from benchling_sdk.services.v2.base_service import BaseService


class DnaSequenceService(BaseService):
    """
    DNA Sequences.

    DNA sequences are the bread and butter of the Benchling Molecular Biology suite. On Benchling, these are
    comprised of a string of nucleotides and collections of other attributes, such as annotations and primers.

    See https://benchling.com/api/reference#/DNA%20Sequences
    """

    @api_method
    def get_by_id(self, dna_sequence_id: str, returning: Optional[Iterable[str]] = None) -> DnaSequence:
        """
        Get a DNA sequence.

        See https://benchling.com/api/reference#/DNA%20Sequences/getDNASequence
        """
        returning_string = optional_array_query_param(returning)
        response = get_dna_sequence.sync_detailed(
            client=self.client, dna_sequence_id=dna_sequence_id, returning=none_as_unset(returning_string)
        )
        return model_from_detailed(response)

    @api_method
    def _dna_sequences_page(
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
        sort: Optional[ListDNASequencesSort] = None,
        ids: Optional[Iterable[str]] = None,
        entity_registry_ids_any_of: Optional[Iterable[str]] = None,
        name_includes: Optional[str] = None,
        names_any_of: Optional[Iterable[str]] = None,
        names_any_of_case_sensitive: Optional[Iterable[str]] = None,
        creator_ids: Optional[Iterable[str]] = None,
        schema_fields: Optional[Dict[str, Any]] = None,
        page_size: Optional[int] = None,
        next_token: Optional[NextToken] = None,
        author_idsany_of: Optional[Iterable[str]] = None,
        returning: Optional[Iterable[str]] = None,
    ) -> Response[DnaSequencesPaginatedList]:
        response = list_dna_sequences.sync_detailed(
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
            schema_fields=none_as_unset(schema_fields_query_param(schema_fields)),
            entity_registry_idsany_of=none_as_unset(optional_array_query_param(entity_registry_ids_any_of)),
            name_includes=none_as_unset(name_includes),
            namesany_of=none_as_unset(optional_array_query_param(names_any_of)),
            namesany_ofcase_sensitive=none_as_unset(optional_array_query_param(names_any_of_case_sensitive)),
            creator_ids=none_as_unset(optional_array_query_param(creator_ids)),
            page_size=none_as_unset(page_size),
            next_token=none_as_unset(next_token),
            author_idsany_of=none_as_unset(optional_array_query_param(author_idsany_of)),
            returning=none_as_unset(optional_array_query_param(returning)),
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
        creator_ids: Optional[Iterable[str]] = None,
        schema_fields: Optional[Dict[str, Any]] = None,
        sort: Optional[Union[str, ListDNASequencesSort]] = None,
        page_size: Optional[int] = None,
        author_idsany_of: Optional[Iterable[str]] = None,
        returning: Optional[Iterable[str]] = None,
    ) -> PageIterator[DnaSequence]:
        """
        List DNA sequences.

        See https://benchling.com/api/reference#/DNA%20Sequences/listDNASequences
        """
        check_for_csv_bug_fix("mentioned_in", mentioned_in)
        check_for_csv_bug_fix("mentions", mentions)

        def api_call(next_token: NextToken) -> Response[DnaSequencesPaginatedList]:
            return self._dna_sequences_page(
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
                creator_ids=creator_ids,
                schema_fields=schema_fields,
                sort=_translate_to_string_enum(ListDNASequencesSort, sort),
                page_size=page_size,
                next_token=next_token,
                author_idsany_of=author_idsany_of,
                returning=returning,
            )

        def results_extractor(body: DnaSequencesPaginatedList) -> Optional[List[DnaSequence]]:
            return body.dna_sequences

        return PageIterator(api_call, results_extractor)

    @api_method
    def create(self, dna_sequence: DnaSequenceCreate) -> DnaSequence:
        """
        Create a DNA sequence.

        See https://benchling.com/api/reference#/DNA%20Sequences/createDNASequence
        """
        response = create_dna_sequence.sync_detailed(client=self.client, json_body=dna_sequence)
        return model_from_detailed(response)

    @api_method
    def update(self, dna_sequence_id: str, dna_sequence: DnaSequenceUpdate) -> DnaSequence:
        """
        Update a DNA sequence.

        See https://benchling.com/api/reference#/DNA%20Sequences/updateDNASequence
        """
        response = update_dna_sequence.sync_detailed(
            client=self.client, dna_sequence_id=dna_sequence_id, json_body=dna_sequence
        )
        return model_from_detailed(response)

    @api_method
    def archive(
        self, dna_sequence_ids: Iterable[str], reason: EntityArchiveReason
    ) -> DnaSequencesArchivalChange:
        """
        Archive DNA sequences.

        See https://benchling.com/api/reference#/DNA%20Sequences/archiveDNASequences
        """
        archive_request = DnaSequencesArchive(reason=reason, dna_sequence_ids=list(dna_sequence_ids))
        response = archive_dna_sequences.sync_detailed(client=self.client, json_body=archive_request)
        return model_from_detailed(response)

    @api_method
    def unarchive(self, dna_sequence_ids: Iterable[str]) -> DnaSequencesArchivalChange:
        """
        Unarchive DNA sequences.

        See https://benchling.com/api/reference#/DNA%20Sequences/unarchiveDNASequences
        """
        unarchive_request = DnaSequencesUnarchive(dna_sequence_ids=list(dna_sequence_ids))
        response = unarchive_dna_sequences.sync_detailed(client=self.client, json_body=unarchive_request)
        return model_from_detailed(response)

    @api_method
    def bulk_get(
        self, dna_sequence_ids: Iterable[str], returning: Optional[Iterable[str]] = None
    ) -> Optional[List[DnaSequence]]:
        """
        Bulk get DNA sequences.

        See https://benchling.com/api/reference#/DNA%20Sequences/bulkGetDNASequences
        """
        dna_sequence_id_string = ",".join(dna_sequence_ids)
        returning_string = optional_array_query_param(returning)
        response = bulk_get_dna_sequences.sync_detailed(
            client=self.client,
            dna_sequence_ids=dna_sequence_id_string,
            returning=none_as_unset(returning_string),
        )
        dna_sequences_results = model_from_detailed(response)
        return dna_sequences_results.dna_sequences

    @api_method
    def bulk_create(
        self, dna_sequences: Iterable[DnaSequenceBulkCreate]
    ) -> TaskHelper[BulkCreateDnaSequencesAsyncTaskResponse]:
        """
        Bulk create DNA sequences.

        See https://benchling.com/api/reference#/DNA%20Sequences/bulkCreateDNASequences
        """
        body = DnaSequencesBulkCreateRequest(list(dna_sequences))
        response = bulk_create_dna_sequences.sync_detailed(client=self.client, json_body=body)
        return self._task_helper_from_response(response, BulkCreateDnaSequencesAsyncTaskResponse)

    @api_method
    def bulk_update(
        self, dna_sequences: Iterable[DnaSequenceBulkUpdate]
    ) -> TaskHelper[BulkUpdateDnaSequencesAsyncTaskResponse]:
        """
        Bulk update DNA sequences.

        See https://benchling.com/api/reference#/DNA%20Sequences/bulkUpdateDNASequences
        """
        body = DnaSequencesBulkUpdateRequest(list(dna_sequences))
        response = bulk_update_dna_sequences.sync_detailed(client=self.client, json_body=body)
        return self._task_helper_from_response(response, BulkUpdateDnaSequencesAsyncTaskResponse)

    @api_method
    def autofill_parts(self, dna_sequence_ids: Iterable[str]) -> TaskHelper[EmptyTaskResponse]:
        """
        Autofill DNA sequence parts.

        See https://benchling.com/api/reference#/DNA%20Sequences/autofillDNASequenceParts
        """
        body = AutofillSequences(dna_sequence_ids=list(dna_sequence_ids))
        response = autofill_dna_sequence_parts.sync_detailed(client=self.client, json_body=body)
        return self._task_helper_from_response(response, EmptyTaskResponse)

    @api_method
    def autofill_transcriptions(self, dna_sequence_ids: Iterable[str]) -> TaskHelper[EmptyTaskResponse]:
        """
        Autofill DNA sequence transcriptions.

        See https://benchling.com/api/reference#/DNA%20Sequences/autofillDNASequenceTranscriptions
        """
        body = AutofillSequences(dna_sequence_ids=list(dna_sequence_ids))
        response = autofill_dna_sequence_transcriptions.sync_detailed(client=self.client, json_body=body)
        return self._task_helper_from_response(response, EmptyTaskResponse)

    @api_method
    def autofill_translations(self, dna_sequence_ids: Iterable[str]) -> TaskHelper[EmptyTaskResponse]:
        """
        Autofill DNA sequence translations.

        See https://benchling.com/api/reference#/DNA%20Sequences/autofillDNASequenceTranslations
        """
        body = AutofillSequences(dna_sequence_ids=list(dna_sequence_ids))
        response = autofill_dna_sequence_translations.sync_detailed(client=self.client, json_body=body)
        return self._task_helper_from_response(response, EmptyTaskResponse)

    @api_method
    def auto_annotate(self, auto_annotate: AutoAnnotateDnaSequences) -> TaskHelper[EmptyTaskResponse]:
        """
        Auto-annotate DNA sequences with matching features from specified Feature Libraries.

        See https://benchling.com/api/reference#/DNA%20Sequences/autoAnnotateDnaSequences
        """
        response = auto_annotate_dna_sequences.sync_detailed(client=self.client, json_body=auto_annotate)
        return self._task_helper_from_response(response, EmptyTaskResponse)

    @api_method
    def upsert(self, entity_registry_id: str, dna_sequence: DnaSequenceUpsertRequest) -> DnaSequence:
        """
        Create or modify a DNA sequence.

        See https://benchling.com/api/reference#/DNA%20Sequences/upsertDNASequence
        """
        response = upsert_dna_sequence.sync_detailed(
            client=self.client, entity_registry_id=entity_registry_id, json_body=dna_sequence
        )
        return model_from_detailed(response)

    @api_method
    def bulk_upsert(
        self, body: DnaSequencesBulkUpsertRequest, returning: Optional[Iterable[str]] = None
    ) -> TaskHelper[BulkUpdateDnaSequencesAsyncTaskResponse]:
        """
        Bulk create or update DNA sequences.

        See https://benchling.com/api/reference#/DNA%20Sequences/bulkUpsertDnaSequences
        """
        returning_string = optional_array_query_param(returning)
        response = bulk_upsert_dna_sequences.sync_detailed(
            client=self.client, json_body=body, returning=none_as_unset(returning_string)
        )
        return self._task_helper_from_response(response, BulkUpdateDnaSequencesAsyncTaskResponse)

    @api_method
    def match_bases(self, match_bases_request: MatchBasesRequest) -> DnaSequencesPaginatedList:
        """
        Match bases.

        Returns DNA Sequences that exactly match the provided bases.

        See https://benchling.com/api/reference#/DNA%20Sequences/matchBasesDnaSequences
        """
        response = match_bases_dna_sequences.sync_detailed(
            client=self.client,
            json_body=match_bases_request,
        )
        return model_from_detailed(response)

    @api_method
    def search_bases(self, search_bases_request: SearchBasesRequest) -> DnaSequencesPaginatedList:
        """
        Search bases.

        Returns DNA Sequences that contain the provided bases.
        Search indexing is asynchronous, so results may be not be available immediately after creation.

        See https://benchling.com/api/reference#/DNA%20Sequences/searchDnaSequences
        """
        response = search_dna_sequences.sync_detailed(
            client=self.client,
            json_body=search_bases_request,
        )
        return model_from_detailed(response)

    @api_method
    def find_matching_regions(
        self, find_matching_region: DnaSequencesFindMatchingRegion
    ) -> TaskHelper[FindMatchingRegionsDnaAsyncTaskResponse]:
        """
        Find matching regions for DNA sequences.

        See https://benchling.com/api/v2/reference#/DNA%20Sequences/findMatchingRegionsDnaSequences
        """
        response = find_matching_regions_dna_sequences.sync_detailed(
            client=self.client, json_body=find_matching_region
        )
        return self._task_helper_from_response(response, FindMatchingRegionsDnaAsyncTaskResponse)

    @api_method
    def optimize_codons(self, optimize_request: OptimizeCodons) -> TaskHelper[EmptyTaskResponse]:
        """
        Create codon-optimized DNA sequences.

        See https://benchling.com/api/reference#/DNA%20Sequences/optimizeCodons
        """
        response = optimize_codons.sync_detailed(client=self.client, json_body=optimize_request)
        return self._task_helper_from_response(response, EmptyTaskResponse)

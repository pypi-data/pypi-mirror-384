from typing import Iterable, List, Optional, Union

from benchling_api_client.v2.stable.api.assay_results import (
    abort_assay_results_transaction,
    archive_assay_results,
    bulk_create_assay_results,
    bulk_get_assay_results,
    commit_assay_results_transaction,
    create_assay_results,
    create_assay_results_in_transaction,
    create_assay_results_transaction,
    get_assay_result,
    list_assay_results,
    unarchive_assay_results,
)
from benchling_api_client.v2.stable.types import UNSET, Unset
from benchling_api_client.v2.types import Response

from benchling_sdk.errors import raise_for_status
from benchling_sdk.helpers.constants import _translate_to_string_enum
from benchling_sdk.helpers.decorators import api_method
from benchling_sdk.helpers.pagination_helpers import NextToken, PageIterator
from benchling_sdk.helpers.response_helpers import model_from_detailed
from benchling_sdk.helpers.serialization_helpers import (
    array_query_param,
    none_as_unset,
    optional_array_query_param,
)
from benchling_sdk.helpers.task_helpers import TaskHelper
from benchling_sdk.helpers.transaction_manager import TransactionManager
from benchling_sdk.models import (
    AssayResult,
    AssayResultCreate,
    AssayResultIdsRequest,
    AssayResultIdsResponse,
    AssayResultsArchive,
    AssayResultsArchiveReason,
    AssayResultsBulkCreateInTableRequest,
    AssayResultsBulkCreateRequest,
    AssayResultsCreateResponse,
    AssayResultsPaginatedList,
    AssayResultTransactionCreateResponse,
    ListAssayResultsSort,
)
from benchling_sdk.services.v2.base_service import BaseService


class AssayResultService(BaseService):
    """
    Assay Results.

    Results represent the output of assays that have been performed. You can customize the schemas of results to
    fit your needs. Results can link to runs, batches, and other types.

    See https://benchling.com/api/reference#/Assay%20Results
    """

    @api_method
    def get_by_id(self, assay_result_id: str) -> AssayResult:
        """
        Get a result.

        See https://benchling.com/api/reference#/Assay%20Results/getAssayResult
        """
        response = get_assay_result.sync_detailed(client=self.client, assay_result_id=assay_result_id)
        return model_from_detailed(response)

    @api_method
    def _assay_results_page(
        self,
        schema_id: Optional[str] = None,
        min_created_time: Optional[int] = None,
        max_created_time: Optional[int] = None,
        entity_ids: Optional[Iterable[str]] = None,
        assay_run_ids: Optional[Iterable[str]] = None,
        next_token: Optional[NextToken] = None,
        page_size: Optional[int] = None,
        ids: Optional[Iterable[str]] = None,
        storage_ids: Optional[Iterable[str]] = None,
        created_atgt: Optional[str] = None,
        created_atgte: Optional[str] = None,
        created_atlt: Optional[str] = None,
        created_atlte: Optional[str] = None,
        modified_atgt: Optional[str] = None,
        modified_atgte: Optional[str] = None,
        modified_atlt: Optional[str] = None,
        modified_atlte: Optional[str] = None,
        automation_output_processor_id: Optional[str] = None,
        archive_reason: Optional[str] = None,
        sort: Optional[ListAssayResultsSort] = None,
    ) -> Response[AssayResultsPaginatedList]:
        entity_ids_string = optional_array_query_param(entity_ids)
        assay_run_ids_string = optional_array_query_param(assay_run_ids)
        response = list_assay_results.sync_detailed(
            client=self.client,
            schema_id=none_as_unset(schema_id),
            min_created_time=none_as_unset(min_created_time),
            max_created_time=none_as_unset(max_created_time),
            entity_ids=none_as_unset(entity_ids_string),
            assay_run_ids=none_as_unset(assay_run_ids_string),
            ids=none_as_unset(optional_array_query_param(ids)),
            storage_ids=none_as_unset(optional_array_query_param(storage_ids)),
            next_token=none_as_unset(next_token),
            page_size=none_as_unset(page_size),
            created_atgt=none_as_unset(created_atgt),
            created_atgte=none_as_unset(created_atgte),
            created_atlt=none_as_unset(created_atlt),
            created_atlte=none_as_unset(created_atlte),
            modified_atgt=none_as_unset(modified_atgt),
            modified_atgte=none_as_unset(modified_atgte),
            modified_atlt=none_as_unset(modified_atlt),
            modified_atlte=none_as_unset(modified_atlte),
            automation_output_processor_id=none_as_unset(automation_output_processor_id),
            archive_reason=none_as_unset(archive_reason),
            sort=none_as_unset(sort),
        )
        raise_for_status(response)
        return response

    def list(
        self,
        schema_id: Optional[str] = None,
        min_created_time: Optional[int] = None,
        max_created_time: Optional[int] = None,
        entity_ids: Optional[Iterable[str]] = None,
        assay_run_ids: Optional[Iterable[str]] = None,
        page_size: Optional[int] = None,
        ids: Optional[Iterable[str]] = None,
        storage_ids: Optional[Iterable[str]] = None,
        created_atgt: Optional[str] = None,
        created_atgte: Optional[str] = None,
        created_atlt: Optional[str] = None,
        created_atlte: Optional[str] = None,
        modified_atgt: Optional[str] = None,
        modified_atgte: Optional[str] = None,
        modified_atlt: Optional[str] = None,
        modified_atlte: Optional[str] = None,
        automation_output_processor_id: Optional[str] = None,
        archive_reason: Optional[str] = None,
        sort: Optional[Union[str, ListAssayResultsSort]] = None,
    ) -> PageIterator[AssayResult]:
        """
        List results.

        See https://benchling.com/api/reference#/Assay%20Results/listAssayResults
        """

        def api_call(next_token: NextToken) -> Response[AssayResultsPaginatedList]:
            return self._assay_results_page(
                schema_id=schema_id,
                min_created_time=min_created_time,
                max_created_time=max_created_time,
                entity_ids=entity_ids,
                assay_run_ids=assay_run_ids,
                ids=ids,
                storage_ids=storage_ids,
                created_atgt=created_atgt,
                created_atgte=created_atgte,
                created_atlt=created_atlt,
                created_atlte=created_atlte,
                modified_atgt=modified_atgt,
                modified_atgte=modified_atgte,
                modified_atlt=modified_atlt,
                modified_atlte=modified_atlte,
                automation_output_processor_id=automation_output_processor_id,
                archive_reason=archive_reason,
                next_token=next_token,
                page_size=page_size,
                sort=_translate_to_string_enum(ListAssayResultsSort, sort),
            )

        def results_extractor(body: AssayResultsPaginatedList) -> Optional[List[AssayResult]]:
            return body.assay_results

        return PageIterator(api_call, results_extractor)

    @api_method
    def bulk_get(self, assay_result_ids: Iterable[str]) -> Optional[List[AssayResult]]:
        """
        Bulk get assay results.

        Up to 200 IDs can be specified at once.

        See https://benchling.com/api/reference#/Assay%20Results/bulkGetAssayResults
        """
        result_ids_string = array_query_param(assay_result_ids)
        response = bulk_get_assay_results.sync_detailed(
            client=self.client, assay_result_ids=result_ids_string
        )
        results_list = model_from_detailed(response)
        return results_list.assay_results

    @api_method
    def create(self, assay_results: Iterable[AssayResultCreate]) -> AssayResultsCreateResponse:
        """
        Create 1 or more results.

        See https://benchling.com/api/reference#/Assay%20Results/createAssayResults
        """
        create_results = AssayResultsBulkCreateRequest(assay_results=list(assay_results))
        response = create_assay_results.sync_detailed(client=self.client, json_body=create_results)
        return model_from_detailed(response)

    @api_method
    def bulk_create(
        self, assay_results: Iterable[AssayResultCreate], table_id: Optional[str] = None
    ) -> TaskHelper[AssayResultsCreateResponse]:
        """
        Create 1 or more results.

        See https://benchling.com/api/reference#/Assay%20Results/bulkCreateAssayResults
        """
        request_body = AssayResultsBulkCreateInTableRequest(
            assay_results=list(assay_results), **({"table_id": table_id} if table_id else {})
        )
        response = bulk_create_assay_results.sync_detailed(client=self.client, json_body=request_body)
        return self._task_helper_from_response(response, AssayResultsCreateResponse)

    @api_method
    def archive(
        self,
        assay_result_ids: Iterable[str],
        reason: Union[Unset, AssayResultsArchiveReason] = UNSET,
    ) -> AssayResultIdsResponse:
        """
        Archive assay results.

        Only results that have not been added to a Notebook Entry can be Archived.
        Once results are attached to a notebook entry, they are tracked in the
        history of that notebook entry, and cannot be archived.

        See https://benchling.com/api/reference#/Assay%20Results/archiveAssayResults
        """
        archive_request = AssayResultsArchive(assay_result_ids=list(assay_result_ids), reason=reason)
        response = archive_assay_results.sync_detailed(
            client=self.client, json_body=archive_request
        )
        return model_from_detailed(response)

    @api_method
    def unarchive(self, assay_result_ids: Iterable[str]) -> AssayResultIdsResponse:
        """
        Unarchive assay results.

        See https://benchling.com/api/reference#/Assay%20Results/unarchiveAssayResults
        """
        unarchive_request = AssayResultIdsRequest(assay_result_ids=list(assay_result_ids))
        response = unarchive_assay_results.sync_detailed(client=self.client, json_body=unarchive_request)
        return model_from_detailed(response)

    @api_method
    def create_transaction(self) -> AssayResultTransactionCreateResponse:
        """
        Create a transaction.

        See https://benchling.com/api/reference#/Assay%20Results/createAssayResultsTransaction
        """
        response = create_assay_results_transaction.sync_detailed(client=self.client)
        return model_from_detailed(response)

    @api_method
    def create_results_in_transaction(
        self, transaction_id: str, assay_results: Iterable[AssayResultCreate]
    ) -> AssayResultsCreateResponse:
        """
        Create results in a transaction.

        See https://benchling.com/api/reference#/Assay%20Results/createAssayResultsInTransaction
        """
        create_request = AssayResultsBulkCreateRequest(assay_results=list(assay_results))
        response = create_assay_results_in_transaction.sync_detailed(
            client=self.client, transaction_id=transaction_id, json_body=create_request
        )
        return model_from_detailed(response)

    @api_method
    def commit_transaction(self, transaction_id: str) -> AssayResultTransactionCreateResponse:
        """
        Commit results in an active transaction.

        Committing a transaction will cause all results that have been uploaded to be saved and visible to others.

        See https://benchling.com/api/reference#/Assay%20Results/commitAssayResultsTransaction
        """
        response = commit_assay_results_transaction.sync_detailed(
            client=self.client, transaction_id=transaction_id
        )
        return model_from_detailed(response)

    @api_method
    def abort_transaction(self, transaction_id: str) -> AssayResultTransactionCreateResponse:
        """
        Abort a transaction.

        Aborting a transaction will discard all uploaded results.

        See https://benchling.com/api/reference#/Assay%20Results/abortAssayResultsTransaction
        """
        response = abort_assay_results_transaction.sync_detailed(
            client=self.client, transaction_id=transaction_id
        )
        return model_from_detailed(response)

    def transaction_manager(self) -> TransactionManager:
        """
        Create a Python context manager for adding results within a transaction.

        When the context exits, the transaction manager will attempt to commit
        the transaction.

        If an unhandled error occurs within the context, the transaction manager
        will automatically attempt to abort the transaction.

        :return: A Python context manager for the transaction
        :rtype: TransactionManager
        """

        def create_trans() -> str:
            return self.create_transaction().id

        def abort_trans(transaction_id: str) -> str:
            return self.abort_transaction(transaction_id=transaction_id).id

        def commit_trans(transaction_id: str) -> str:
            return self.commit_transaction(transaction_id=transaction_id).id

        def append_rows(transaction_id: str, rows: Iterable[AssayResultCreate]) -> List[str]:
            return self.create_results_in_transaction(
                transaction_id=transaction_id, assay_results=rows
            ).assay_results

        return TransactionManager(
            create_transaction_call=create_trans,
            abort_transaction_call=abort_trans,
            commit_transaction_call=commit_trans,
            append_row_call=append_rows,
        )

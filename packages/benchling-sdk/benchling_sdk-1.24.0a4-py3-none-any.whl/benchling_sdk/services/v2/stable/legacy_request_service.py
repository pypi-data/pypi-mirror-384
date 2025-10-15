from typing import Iterable, List, Optional

from benchling_api_client.v2.stable.api.legacy_requests import (
    bulk_create_request_tasks,
    bulk_get_requests,
    bulk_update_request_tasks,
    create_request,
    execute_requests_sample_groups,
    get_request,
    get_request_fulfillment,
    get_request_response,
    list_request_fulfillments,
    list_requests,
    patch_request,
)
from benchling_api_client.v2.types import Response

from benchling_sdk.errors import raise_for_status
from benchling_sdk.helpers.decorators import api_method
from benchling_sdk.helpers.pagination_helpers import NextToken, PageIterator
from benchling_sdk.helpers.response_helpers import model_from_detailed
from benchling_sdk.helpers.serialization_helpers import none_as_unset, optional_array_query_param
from benchling_sdk.models import (
    Request,
    RequestCreate,
    RequestFulfillment,
    RequestFulfillmentsPaginatedList,
    RequestResponse,
    RequestsPaginatedList,
    RequestStatus,
    RequestTaskBase,
    RequestTasksBulkCreate,
    RequestTasksBulkCreateRequest,
    RequestTasksBulkCreateResponse,
    RequestTasksBulkUpdateRequest,
    RequestTasksBulkUpdateResponse,
    RequestUpdate,
    SampleGroupsStatusUpdate,
)
from benchling_sdk.services.v2.base_service import BaseService


class LegacyRequestService(BaseService):
    """
    Legacy Requests.

    Legacy Requests allow scientists and teams to collaborate around experimental assays and workflows.

    See https://benchling.com/api/reference#/Legacy%20Requests
    """

    @api_method
    def get_by_id(self, request_id: str, returning: Optional[Iterable[str]] = None) -> Request:
        """
        Get a Legacy Request by ID.

        See https://benchling.com/api/reference#/Legacy%20Requests/getRequest
        """
        returning_string = optional_array_query_param(returning)
        response = get_request.sync_detailed(
            client=self.client, request_id=request_id, returning=none_as_unset(returning_string)
        )
        return model_from_detailed(response)

    @api_method
    def _requests_page(
        self,
        schema_id: str,
        request_status: Optional[RequestStatus] = None,
        min_created_time: Optional[int] = None,
        max_created_time: Optional[int] = None,
        next_token: Optional[NextToken] = None,
        page_size: Optional[int] = None,
        returning: Optional[Iterable[str]] = None,
    ) -> Response[RequestsPaginatedList]:
        response = list_requests.sync_detailed(
            client=self.client,
            schema_id=schema_id,
            request_status=none_as_unset(request_status),
            min_created_time=none_as_unset(min_created_time),
            max_created_time=none_as_unset(max_created_time),
            next_token=none_as_unset(next_token),
            page_size=none_as_unset(page_size),
            returning=none_as_unset(optional_array_query_param(returning)),
        )
        raise_for_status(response)
        return response

    def list(
        self,
        schema_id: str,
        request_status: Optional[RequestStatus] = None,
        min_created_time: Optional[int] = None,
        max_created_time: Optional[int] = None,
        page_size: Optional[int] = None,
        returning: Optional[Iterable[str]] = None,
    ) -> PageIterator[Request]:
        """
        List Requests.

        See https://benchling.com/api/reference#/Legacy%20Requests/listRequests
        """

        def api_call(next_token: NextToken) -> Response[RequestsPaginatedList]:
            return self._requests_page(
                schema_id=schema_id,
                request_status=request_status,
                min_created_time=min_created_time,
                max_created_time=max_created_time,
                next_token=next_token,
                page_size=page_size,
                returning=returning,
            )

        def results_extractor(body: RequestsPaginatedList) -> Optional[List[Request]]:
            return body.requests

        return PageIterator(api_call, results_extractor)

    @api_method
    def bulk_get(
        self,
        *,
        request_ids: Optional[Iterable[str]] = None,
        display_ids: Optional[Iterable[str]] = None,
        returning: Optional[Iterable[str]] = None
    ) -> Optional[List[Request]]:
        """
        Bulk get Requests.

        See https://benchling.com/api/reference#/Legacy%20Requests/bulkGetRequests
        """
        request_id_string = optional_array_query_param(request_ids)
        display_id_string = optional_array_query_param(display_ids)
        returning_string = optional_array_query_param(returning)
        response = bulk_get_requests.sync_detailed(
            client=self.client,
            request_ids=none_as_unset(request_id_string),
            display_ids=none_as_unset(display_id_string),
            returning=none_as_unset(returning_string),
        )
        requests_list = model_from_detailed(response)
        return requests_list.requests

    @api_method
    def request_response(self, request_id: str) -> RequestResponse:
        """
        Get a Legacy Request's response.

        See https://benchling.com/api/reference#/Legacy%20Requests/getRequestResponse
        """
        response = get_request_response.sync_detailed(client=self.client, request_id=request_id)
        return model_from_detailed(response)

    @api_method
    def create(self, request: RequestCreate) -> Request:
        """
        Create a Legacy Request.

        See https://benchling.com/api/reference#/Legacy%20Requests/createRequest
        """
        response = create_request.sync_detailed(client=self.client, json_body=request)
        return model_from_detailed(response)

    @api_method
    def update(self, request_id: str, request: RequestUpdate) -> Request:
        """
        Update a Legacy Request.

        See https://benchling.com/api/reference#/Legacy%20Requests/patchRequest
        """
        response = patch_request.sync_detailed(client=self.client, request_id=request_id, json_body=request)
        return model_from_detailed(response)

    @api_method
    def execute_sample_groups(self, request_id: str, sample_groups: SampleGroupsStatusUpdate) -> None:
        """
        Update the status of sample groups in a Legacy Request.

        See https://benchling.com/api/reference#/Legacy%20Requests/executeRequestsSampleGroups
        """
        response = execute_requests_sample_groups.sync_detailed(
            client=self.client, request_id=request_id, json_body=sample_groups
        )
        return model_from_detailed(response)

    @api_method
    def request_fulfillment(self, request_fulfillment_id: str) -> RequestFulfillment:
        """
        Get a Legacy Request's fulfillment.

        See https://benchling.com/api/reference#/Legacy%20Requests/getRequestFulfillment
        """
        response = get_request_fulfillment.sync_detailed(
            client=self.client, request_fulfillment_id=request_fulfillment_id
        )
        return model_from_detailed(response)

    @api_method
    def _entry_request_fulfillments_page(
        self,
        entry_id: str,
        modified_at: Optional[str] = None,
        next_token: Optional[NextToken] = None,
        page_size: Optional[int] = None,
    ) -> Response[RequestFulfillmentsPaginatedList]:
        response = list_request_fulfillments.sync_detailed(
            client=self.client,
            entry_id=entry_id,
            modified_at=none_as_unset(modified_at),
            next_token=none_as_unset(next_token),
            page_size=none_as_unset(page_size),
        )
        raise_for_status(response)
        return response  # type: ignore

    def entry_request_fulfillments(
        self, entry_id: str, modified_at: Optional[str] = None, page_size: Optional[int] = None
    ) -> PageIterator[RequestFulfillment]:
        """
        List Legacy Request Fulfillments.

        See https://benchling.com/api/reference#/Legacy%20Requests/listRequestFulfillments
        """

        def api_call(next_token: NextToken) -> Response[RequestFulfillmentsPaginatedList]:
            return self._entry_request_fulfillments_page(
                entry_id=entry_id,
                modified_at=modified_at,
                next_token=next_token,
                page_size=page_size,
            )

        def results_extractor(body: RequestFulfillmentsPaginatedList) -> Optional[List[RequestFulfillment]]:
            return body.request_fulfillments

        return PageIterator(api_call, results_extractor)

    @api_method
    def bulk_create_tasks(
        self, request_id: str, tasks: Iterable[RequestTasksBulkCreate]
    ) -> RequestTasksBulkCreateResponse:
        """
        Create tasks for a Legacy Request.

        See https://benchling.com/api/reference#/Legacy%20Requests/bulkCreateRequestTasks
        """
        create = RequestTasksBulkCreateRequest(tasks=list(tasks))
        response = bulk_create_request_tasks.sync_detailed(
            client=self.client, request_id=request_id, json_body=create
        )
        return model_from_detailed(response)

    @api_method
    def bulk_update_tasks(
        self, request_id: str, tasks: Iterable[RequestTaskBase]
    ) -> RequestTasksBulkUpdateResponse:
        """
        Update tasks for a Legacy Request.

        See https://benchling.com/api/reference#/Legacy%20Requests/bulkUpdateRequestTasks
        """
        update = RequestTasksBulkUpdateRequest(tasks=list(tasks))
        response = bulk_update_request_tasks.sync_detailed(
            client=self.client, request_id=request_id, json_body=update
        )
        return model_from_detailed(response)

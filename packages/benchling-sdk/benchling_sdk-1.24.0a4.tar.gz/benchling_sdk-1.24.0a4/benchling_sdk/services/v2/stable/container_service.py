from typing import Any, Dict, Iterable, List, Optional, Union

from benchling_api_client.v2.stable.api.containers import (
    archive_containers,
    bulk_create_containers,
    bulk_get_containers,
    bulk_update_containers,
    checkin_containers,
    checkout_containers,
    create_container,
    delete_container_content,
    get_container,
    get_container_content,
    list_container_contents,
    list_containers,
    print_labels,
    reserve_containers,
    transfer_into_container,
    transfer_into_containers,
    unarchive_containers,
    update_container,
    update_container_content,
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
from benchling_sdk.helpers.task_helpers import TaskHelper
from benchling_sdk.models import (
    BulkCreateContainersAsyncTaskResponse,
    BulkUpdateContainersAsyncTaskResponse,
    Container,
    ContainerBulkUpdateItem,
    ContainerContent,
    ContainerContentUpdate,
    ContainerCreate,
    ContainersArchivalChange,
    ContainersArchive,
    ContainersArchiveReason,
    ContainersBulkCreateRequest,
    ContainersBulkUpdateRequest,
    ContainersCheckin,
    ContainersCheckout,
    ContainersPaginatedList,
    ContainersUnarchive,
    ContainerTransfer,
    ContainerUpdate,
    ListContainersCheckoutStatus,
    ListContainersSort,
    Measurement,
    MultipleContainersTransfer,
    MultipleContainersTransfersList,
    PrintLabels,
    SampleRestrictionStatus,
    TransfersAsyncTaskResponse,
)
from benchling_sdk.services.v2.base_service import BaseService


class ContainerService(BaseService):
    """
    Containers.

    Containers are the backbone of sample management in Benchling. They represent physical containers, such as
    tubes or wells, that hold quantities of biological samples (represented by the batches inside the container).
    The container itself tracks its total volume, and the concentration of every batch inside of it.

    Containers are all associated with schemas, which define the type of the container (e.g. "Tube") along with the
    fields that are tracked.

    Like all storage, every container has a barcode that is unique across the registry.

    See https://benchling.com/api/reference#/Containers
    """

    @api_method
    def get_by_id(self, container_id: str, returning: Optional[Iterable[str]] = None) -> Container:
        """
        Get a container by ID.

        See https://benchling.com/api/reference#/Containers/getContainer
        """
        returning_string = optional_array_query_param(returning)
        response = get_container.sync_detailed(
            client=self.client, container_id=container_id, returning=none_as_unset(returning_string)
        )
        return model_from_detailed(response)

    @api_method
    def _containers_page(
        self,
        *,
        page_size: Optional[int] = 50,
        next_token: Optional[str] = None,
        sort: Optional[ListContainersSort] = None,
        schema_id: Optional[str] = None,
        modified_at: Optional[str] = None,
        created_at: Optional[str] = None,
        name: Optional[str] = None,
        name_includes: Optional[str] = None,
        ancestor_storage_id: Optional[str] = None,
        storage_contents_id: Optional[str] = None,
        storage_contents_ids: Optional[List[str]] = None,
        checkout_status: Optional[ListContainersCheckoutStatus] = None,
        ids: Optional[Iterable[str]] = None,
        barcodes: Optional[Iterable[str]] = None,
        names_any_of: Optional[Iterable[str]] = None,
        names_any_of_case_sensitive: Optional[Iterable[str]] = None,
        creator_ids: Optional[Iterable[str]] = None,
        checkout_assignee_ids_any_of: Optional[Iterable[str]] = None,
        restricted_sample_party_ids_all_of: Optional[Iterable[str]] = None,
        restricted_sample_party_ids_any_of: Optional[Iterable[str]] = None,
        restricted_sample_party_ids_none_of: Optional[Iterable[str]] = None,
        restriction_status: Optional[SampleRestrictionStatus] = None,
        sample_owner_ids_all_of: Optional[Iterable[str]] = None,
        sample_owner_ids_any_of: Optional[Iterable[str]] = None,
        sample_owner_ids_none_of: Optional[Iterable[str]] = None,
        archive_reason: Optional[str] = None,
        schema_fields: Optional[Dict[str, Any]] = None,
        returning: Optional[Iterable[str]] = None,
    ) -> Response[ContainersPaginatedList]:
        response = list_containers.sync_detailed(
            client=self.client,
            sort=none_as_unset(sort),
            schema_id=none_as_unset(schema_id),
            modified_at=none_as_unset(modified_at),
            created_at=none_as_unset(created_at),
            name=none_as_unset(name),
            name_includes=none_as_unset(name_includes),
            ancestor_storage_id=none_as_unset(ancestor_storage_id),
            storage_contents_id=none_as_unset(storage_contents_id),
            storage_contents_ids=none_as_unset(optional_array_query_param(storage_contents_ids)),
            checkout_status=none_as_unset(checkout_status),
            ids=none_as_unset(optional_array_query_param(ids)),
            barcodes=none_as_unset(optional_array_query_param(barcodes)),
            namesany_of=none_as_unset(optional_array_query_param(names_any_of)),
            namesany_ofcase_sensitive=none_as_unset(optional_array_query_param(names_any_of_case_sensitive)),
            creator_ids=none_as_unset(optional_array_query_param(creator_ids)),
            checkout_assignee_idsany_of=none_as_unset(
                optional_array_query_param(checkout_assignee_ids_any_of)
            ),
            restricted_sample_party_idsall_of=none_as_unset(
                optional_array_query_param(restricted_sample_party_ids_all_of)
            ),
            restricted_sample_party_idsany_of=none_as_unset(
                optional_array_query_param(restricted_sample_party_ids_any_of)
            ),
            restricted_sample_party_idsnone_of=none_as_unset(
                optional_array_query_param(restricted_sample_party_ids_none_of)
            ),
            restriction_status=none_as_unset(restriction_status),
            sample_owner_idsall_of=none_as_unset(optional_array_query_param(sample_owner_ids_all_of)),
            sample_owner_idsany_of=none_as_unset(optional_array_query_param(sample_owner_ids_any_of)),
            sample_owner_idsnone_of=none_as_unset(optional_array_query_param(sample_owner_ids_none_of)),
            archive_reason=none_as_unset(archive_reason),
            schema_fields=none_as_unset(schema_fields_query_param(schema_fields)),
            next_token=none_as_unset(next_token),
            page_size=none_as_unset(page_size),
            returning=none_as_unset(optional_array_query_param(returning)),
        )
        raise_for_status(response)
        return response  # type: ignore

    def list(
        self,
        *,
        sort: Optional[Union[str, ListContainersSort]] = None,
        schema_id: Optional[str] = None,
        modified_at: Optional[str] = None,
        created_at: Optional[str] = None,
        name: Optional[str] = None,
        name_includes: Optional[str] = None,
        ancestor_storage_id: Optional[str] = None,
        storage_contents_id: Optional[str] = None,
        storage_contents_ids: Optional[List[str]] = None,
        checkout_status: Optional[ListContainersCheckoutStatus] = None,
        ids: Optional[Iterable[str]] = None,
        barcodes: Optional[Iterable[str]] = None,
        names_any_of: Optional[Iterable[str]] = None,
        names_any_of_case_sensitive: Optional[Iterable[str]] = None,
        creator_ids: Optional[Iterable[str]] = None,
        checkout_assignee_ids_any_of: Optional[Iterable[str]] = None,
        restricted_sample_party_ids_all_of: Optional[Iterable[str]] = None,
        restricted_sample_party_ids_any_of: Optional[Iterable[str]] = None,
        restricted_sample_party_ids_none_of: Optional[Iterable[str]] = None,
        restriction_status: Optional[SampleRestrictionStatus] = None,
        sample_owner_ids_all_of: Optional[Iterable[str]] = None,
        sample_owner_ids_any_of: Optional[Iterable[str]] = None,
        sample_owner_ids_none_of: Optional[Iterable[str]] = None,
        archive_reason: Optional[str] = None,
        schema_fields: Optional[Dict[str, Any]] = None,
        page_size: Optional[int] = None,
        returning: Optional[Iterable[str]] = None,
    ) -> PageIterator[Container]:
        """
        List containers.

        See https://benchling.com/api/reference#/Containers/listContainers
        """
        check_for_csv_bug_fix("storage_contents_ids", storage_contents_ids)

        def api_call(next_token: NextToken) -> Response[ContainersPaginatedList]:
            return self._containers_page(
                sort=_translate_to_string_enum(ListContainersSort, sort),
                schema_id=schema_id,
                modified_at=modified_at,
                created_at=created_at,
                name=name,
                name_includes=name_includes,
                ancestor_storage_id=ancestor_storage_id,
                storage_contents_id=storage_contents_id,
                storage_contents_ids=storage_contents_ids,
                checkout_status=checkout_status,
                ids=ids,
                barcodes=barcodes,
                names_any_of=names_any_of,
                names_any_of_case_sensitive=names_any_of_case_sensitive,
                creator_ids=creator_ids,
                checkout_assignee_ids_any_of=checkout_assignee_ids_any_of,
                restricted_sample_party_ids_all_of=restricted_sample_party_ids_all_of,
                restricted_sample_party_ids_any_of=restricted_sample_party_ids_any_of,
                restricted_sample_party_ids_none_of=restricted_sample_party_ids_none_of,
                restriction_status=restriction_status,
                sample_owner_ids_all_of=sample_owner_ids_all_of,
                sample_owner_ids_any_of=sample_owner_ids_any_of,
                sample_owner_ids_none_of=sample_owner_ids_none_of,
                archive_reason=archive_reason,
                next_token=next_token,
                schema_fields=schema_fields,
                page_size=page_size,
                returning=returning,
            )

        def results_extractor(body: ContainersPaginatedList) -> Optional[List[Container]]:
            return body.containers

        return PageIterator(api_call, results_extractor)

    @api_method
    def bulk_get(
        self,
        *,
        container_ids: Optional[Iterable[str]] = None,
        barcodes: Optional[Iterable[str]] = None,
        returning: Optional[Iterable[str]] = None,
    ) -> Optional[List[Container]]:
        """
        Bulk get containers.

        See https://benchling.com/api/reference#/Containers/bulkGetContainers
        """
        container_id_string = optional_array_query_param(container_ids)
        barcode_string = optional_array_query_param(barcodes)
        returning_string = optional_array_query_param(returning)
        response = bulk_get_containers.sync_detailed(
            client=self.client,
            container_ids=none_as_unset(container_id_string),
            barcodes=none_as_unset(barcode_string),
            returning=none_as_unset(returning_string),
        )
        containers_list = model_from_detailed(response)
        return containers_list.containers

    @api_method
    def bulk_create(
        self, containers: Iterable[ContainerCreate]
    ) -> TaskHelper[BulkCreateContainersAsyncTaskResponse]:
        """
        Bulk create containers.

        See https://benchling.com/api/reference#/Containers/bulkCreateContainers
        """
        body = ContainersBulkCreateRequest(list(containers))
        response = bulk_create_containers.sync_detailed(client=self.client, json_body=body)
        return self._task_helper_from_response(response, BulkCreateContainersAsyncTaskResponse)

    @api_method
    def bulk_update(
        self, containers: Iterable[ContainerBulkUpdateItem]
    ) -> TaskHelper[BulkUpdateContainersAsyncTaskResponse]:
        """
        Bulk update containers.

        See https://benchling.com/api/reference#/Containers/bulkUpdateContainers
        """
        body = ContainersBulkUpdateRequest(list(containers))
        response = bulk_update_containers.sync_detailed(client=self.client, json_body=body)
        return self._task_helper_from_response(response, BulkUpdateContainersAsyncTaskResponse)

    @api_method
    def create(self, container: ContainerCreate) -> Container:
        """
        Create a new container.

        See https://benchling.com/api/reference#/Containers/createContainer
        """
        response = create_container.sync_detailed(client=self.client, json_body=container)
        return model_from_detailed(response)

    @api_method
    def update(self, container_id: str, container: ContainerUpdate) -> Container:
        """
        Update a container.

        See https://benchling.com/api/reference#/Containers/updateContainer
        """
        response = update_container.sync_detailed(
            client=self.client, container_id=container_id, json_body=container
        )
        return model_from_detailed(response)

    @api_method
    def archive(
        self, container_ids: Iterable[str], reason: ContainersArchiveReason, should_remove_barcodes: bool
    ) -> ContainersArchivalChange:
        """
        Archive containers.

        See https://benchling.com/api/reference#/Containers/archiveContainers
        """
        archive_request = ContainersArchive(
            container_ids=list(container_ids), reason=reason, should_remove_barcodes=should_remove_barcodes
        )
        response = archive_containers.sync_detailed(client=self.client, json_body=archive_request)
        return model_from_detailed(response)

    @api_method
    def unarchive(self, container_ids: Iterable[str]) -> ContainersArchivalChange:
        """
        Unarchive containers.

        See https://benchling.com/api/reference#/Containers/unarchiveContainers
        """
        unarchive_request = ContainersUnarchive(container_ids=list(container_ids))
        response = unarchive_containers.sync_detailed(client=self.client, json_body=unarchive_request)
        return model_from_detailed(response)

    @api_method
    def print_labels(self, print_request: PrintLabels) -> None:
        """
        Print labels.

        See https://benchling.com/api/reference#/Containers/printLabels
        """
        response = print_labels.sync_detailed(client=self.client, json_body=print_request)
        raise_for_status(response)

    @api_method
    def contents_by_id(self, container_id: str, containable_id: str) -> ContainerContent:
        """
        Get a container content.

        See https://benchling.com/api/reference#/Containers/getContainerContent
        """
        response = get_container_content.sync_detailed(
            client=self.client, container_id=container_id, containable_id=containable_id
        )
        return model_from_detailed(response)

    @api_method
    def list_contents(self, container_id: str) -> List[ContainerContent]:
        """
        List a container's contents.

        See https://benchling.com/api/reference#/Containers/listContainerContents
        """
        response = list_container_contents.sync_detailed(client=self.client, container_id=container_id)
        contents_list = model_from_detailed(response)
        return contents_list.contents

    @api_method
    def update_contents(
        self, container_id: str, containable_id: str, concentration: Measurement
    ) -> ContainerContent:
        """
        Update a container's content.

        See https://benchling.com/api/reference#/Containers/updateContainerContent
        """
        update = ContainerContentUpdate(concentration=concentration)
        response = update_container_content.sync_detailed(
            client=self.client, container_id=container_id, containable_id=containable_id, json_body=update
        )
        return model_from_detailed(response)

    @api_method
    def delete_contents(self, container_id: str, containable_id: str) -> None:
        """
        Delete a container's content.

        See https://benchling.com/api/reference#/Containers/deleteContainerContent
        """
        response = delete_container_content.sync_detailed(
            client=self.client, container_id=container_id, containable_id=containable_id
        )
        raise_for_status(response)

    @api_method
    def reserve(self, reservation: ContainersCheckout) -> None:
        """
        Reserve containers.

        See https://benchling.com/api/reference#/Containers/reserveContainers
        """
        response = reserve_containers.sync_detailed(client=self.client, json_body=reservation)
        raise_for_status(response)

    @api_method
    def checkout(self, checkout: ContainersCheckout) -> None:
        """
        Check out containers.

        See https://benchling.com/api/reference#/Containers/checkoutContainers
        """
        response = checkout_containers.sync_detailed(client=self.client, json_body=checkout)
        raise_for_status(response)

    @api_method
    def checkin(self, checkin: ContainersCheckin) -> None:
        """
        Check in containers.

        See https://benchling.com/api/reference#/Containers/checkinContainers
        """
        response = checkin_containers.sync_detailed(client=self.client, json_body=checkin)
        raise_for_status(response)

    @api_method
    def transfer_into_container(
        self, destination_container_id: str, transfer_request: ContainerTransfer
    ) -> None:
        """
        Transfer into container.

        See https://benchling.com/api/reference#/Containers/transferIntoContainer
        """
        response = transfer_into_container.sync_detailed(
            client=self.client, destination_container_id=destination_container_id, json_body=transfer_request
        )
        raise_for_status(response)

    @api_method
    def transfer_into_containers(
        self, transfer_requests: Iterable[MultipleContainersTransfer]
    ) -> TaskHelper[TransfersAsyncTaskResponse]:
        """
        Transfer into containers.

        See https://benchling.com/api/reference#/Containers/transferIntoContainers
        """
        multiple_requests = MultipleContainersTransfersList(transfers=list(transfer_requests))
        response = transfer_into_containers.sync_detailed(client=self.client, json_body=multiple_requests)
        return self._task_helper_from_response(response, TransfersAsyncTaskResponse)

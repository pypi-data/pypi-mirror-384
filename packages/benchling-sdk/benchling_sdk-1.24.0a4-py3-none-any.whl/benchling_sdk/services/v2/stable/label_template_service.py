from typing import List, Optional

from benchling_api_client.v2.stable.api.label_templates import list_label_templates

from benchling_sdk.helpers.decorators import api_method
from benchling_sdk.helpers.response_helpers import model_from_detailed
from benchling_sdk.helpers.serialization_helpers import none_as_unset
from benchling_sdk.models import LabelTemplate
from benchling_sdk.services.v2.base_service import BaseService


class LabelTemplateService(BaseService):
    """
    Label Templates.

    List label templates.

    See https://benchling.com/api/reference#/Label%20Templates
    """

    @api_method
    def get_list(self, registry_id: str, name: Optional[str] = None) -> List[LabelTemplate]:
        """
        List label templates.

        See https://benchling.com/api/reference#/Label%20Templates/listLabelTemplates

        :param registry_id: The ID of the registry for which to list label templates
        :param name: The name of the label template
        :return: A list of label templates
        :rtype: List[LabelTemplate]
        """
        response = list_label_templates.sync_detailed(
            client=self.client, registry_id=registry_id, name=none_as_unset(name)
        )
        results = model_from_detailed(response)
        return results.label_templates

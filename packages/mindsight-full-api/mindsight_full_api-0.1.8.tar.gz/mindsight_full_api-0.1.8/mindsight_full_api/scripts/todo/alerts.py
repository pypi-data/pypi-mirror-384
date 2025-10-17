"""This module provide methods to work with areas entity"""

from datetime import date
from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from mindsight_full_api.settings import (
    API_ENDPOINT_ABSENCES,
    API_ENDPOINT_PEOPLE,
    API_ENDPOINT_ALERTS_TYPES,
    DATE_FORMAT,
)
from mindsight_full_api.utils.aux_functions import generate_url


class Absence(ApiEndpoint):
    """This class abstract the absence endpoint methods
    """

    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_ABSENCES)

    def get_list_alerts(
        self,
        search: str = None,
        alert_type: str = None,
        classification: str = None,
        alert_type_active: str = None,
        active: str = None,
        only_last_update: str = None,
        alert_category: str = None,
    ) -> ApiPaginationResponse:
        """Get absence data
        https://full.mindsight.com.br/stone/api/v1/docs/#tag/Alertas/operation/listAlerts

        Args:
            alert_type (str, Mandatory): Area start date
            classification (str, Mandatory): Area start date
            alert_type_active (str, Mandatory): Area start date
            active (str, Mandatory): Area start date
            only_last_update (str, Mandatory): Area start date
            alert_category (str, Mandatory): Area start date
            search
            }
        """

        path = ""
        parameters = {
            "search": search,
            "alert_type": alert_type,
            "classification": classification,
            "alert_type_active": alert_type_active,
            "active": active,
            "only_last_update": only_last_update,
            "alert_category": alert_category,
            "page_size": self.page_size,
        }
        return ApiPaginationResponse(
            **self._base_requests.get(path=path, parameters=parameters).json(),
            headers=self._base_requests.headers,
        )

    def post_create_alert(
        self,
        start_date: date,
        value: str,
        person_id: int,
        alert_type_id: int,
        end_date: date = None,
        notified: str = None,
    ):
        """Create new alert
        Reference:
            https://full.mindsight.com.br/stone/api/v1/docs/#tag/Afastamentos/operation/createAbsence

        Args:
            start_date (date, Mandatory): Area start date
            end_date (date, Optional): Parent area id
            is_approved (bool, Mandatory): Code of area
            type (str, Mandatory): Name of area
            observations (str, Mandatory): Name of area
            number_of_days (int, Mandatory): Name of area
            person (int, Mandatory): Name of area
        """
        path = ""
        data = {
            "start_date": start_date.strftime(DATE_FORMAT),
            "end_date": end_date.strftime(DATE_FORMAT) if end_date else end_date,
            "notified": notified,
            "value": value,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
            "alert_type": generate_url(
                base_path=API_ENDPOINT_ALERTS_TYPES, path=f"/{alert_type_id}"
            ),
        }

        return self._base_requests.post(path=path, data=data)

    def get_alert(
        self,
        _id: int,
        search: str = None,
        alert_type: str = None,
        classification: str = None,
        alert_type_active: str = None,
        active: str = None,
        only_last_update: str = None,
        alert_category: str = None,
    ) -> dict:
        """Get retrieve alert
        Reference:
            https://full.mindsight.com.br/stone/api/v1/docs/#tag/Alertas/operation/retrieveAlert

        Args:
            _id (int, Mandatory): Id of alert to retrieve
            alert_type (str, Mandatory): Area start date
            classification (str, Mandatory): Area start date
            alert_type_active (str, Mandatory): Area start date
            active (str, Mandatory): Area start date
            only_last_update (str, Mandatory): Area start date
            alert_category (str, Mandatory): Area start date
            search
        """
        path = f"/{_id}"
        parameters = {
            "search": search,
            "alert_type": alert_type,
            "classification": classification,
            "alert_type_active": alert_type_active,
            "active": active,
            "only_last_update": only_last_update,
            "alert_category": alert_category,
        }
        return self._base_requests.get(
            path=path,
            parameters=parameters,
        )

    def get_alert_detail_information(
        self,
        _id: int,
    ) -> dict:
        """Get retrieve alert
        Reference:
            https://full.mindsight.com.br/stone/api/v1/docs/#tag/Alertas/operation/alertDetailInformationAlert

        Args:
            _id (int, Mandatory): Id of alert to retrieve
        """
        path = f"/{_id}/alert_detail_information/"
        return self._base_requests.get(
            path=path,
        )

    def get_alert_grouped_type_classification(
        self,
        _id: int,
    ) -> dict:
        """Get retrieve alert
        Reference:
            https://full.mindsight.com.br/stone/api/v1/docs/#tag/Alertas/operation/alertGroupedTypeClassificationAlert

        Args:
            _id (int, Mandatory): Id of alert to retrieve
        """
        path = f"/{_id}/alert_grouped_type_classification/"
        return self._base_requests.get(
            path=path,
        )

    def get_alerts_overview_home_info(
        self,
        _id: int,
    ) -> dict:
        """Get retrieve alert
        Reference:
            https://full.mindsight.com.br/stone/api/v1/docs/#tag/Alertas/operation/retrieveAlert

        Args:
            _id (int, Mandatory): Id of alert to retrieve
        """
        path = f"/{_id}/alerts_overview_home_info/"
        return self._base_requests.get(
            path=path,
        )

    def get_alerts_overview_info(
        self,
        _id: int,
    ) -> dict:
        """Get retrieve alert
        Reference:
            https://full.mindsight.com.br/stone/api/v1/docs/#tag/Alertas/operation/retrieveAlert

        Args:
            _id (int, Mandatory): Id of alert to retrieve
        """
        path = f"/{_id}/alerts_overview_info/"
        return self._base_requests.get(
            path=path,
        )

    def patch_edit_alert(
        self,
        _id: int,
        start_date: date,
        value: int,
        person_id: int,
        alert_type_id: int,
        end_date: date = None,
        notified: bool = False,
        search: str = None,
        alert_type: str = None,
        classification: str = None,
        alert_type_active: str = None,
        active: str = None,
        only_last_update: str = None,
        alert_category: str = None,
    ) -> dict:
        """Edit area and last area record
        Reference:
            https://full.mindsight.com.br/stone/api/v1/docs/#tag/Afastamentos/operation/partialUpdateAbsence

        Args:
            _id (int, Mandatory): Area id
            search (str, Mandatory): Area start date
            alert_type (str, Optional): Parent area id
            classification (str, Mandatory): Code of area
            alert_type_active (str, Mandatory): Name of area
            active (str, Mandatory): Name of area
            only_last_update (str, Mandatory): Name of area
            alert_category (str, Mandatory): Name of area
            start_date (date, Mandatory): Name of area
            end_date (date, Mandatory): Name of area
            notified (bool, Mandatory): Name of area
            value (int, Mandatory): Name of area
            person_id (int, Mandatory): Name of area
            alert_type_id (int, Mandatory): Name of area
        """
        path = f"/{_id}/"
        data = {
            "start_date": start_date.strftime(DATE_FORMAT),
            "end_date": end_date.strftime(DATE_FORMAT) if end_date else end_date,
            "notified": notified,
            "value": value,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
            "alert_type": generate_url(
                base_path=API_ENDPOINT_ALERTS_TYPES, path=f"/{alert_type_id}"
            ),
        }
        parameters = {
            "search": search,
            "alert_type": alert_type,
            "classification": classification,
            "alert_type_active": alert_type_active,
            "active": active,
            "only_last_update": only_last_update,
            "alert_category": alert_category,
        }
        return self._base_requests.patch(path=path, data=data, parameters=parameters)

    def put_edit_alert(
        self,
        _id: int,
        name: str,
        start_date: date,
        value: int,
        person_id: int,
        alert_type_classification_count: int = None,
        end_date: str = None,
        classification: int = None,
        notified: str = None,
        description: str = None,
        high_threshold: int = None,
        medium_threshold: int = None,
        low_threshold: int = None,
        reverse: bool = None,
        category: str = None,
        category_type_key: str = None,
        action_suggestion: str = None,
        relevant_data: str = None,
        action_suggestion_link: str = None,
        action_suggestion_name: str = None,
        action_suggestion_description: str = None,
        action_suggestion_flow_type: str = None,
        search: str = None,
        alert_type: str = None,
        classification_param: str = None,
        alert_type_active: str = None,
        active: str = None,
        only_last_update: str = None,
        alert_category: str = None,
    ) -> dict:
        """Edit absence
        Reference:
            https://full.mindsight.com.br/stone/api/v1/docs/#tag/Alertas/operation/updateAlert

        Args:
            _id (int, Mandatory): Area id
            start_date (date, Mandatory): Area start date
            end_date (date, Optional): Parent area id
            is_approved (bool, Mandatory): Code of area
            type (str, Mandatory): Name of area
            observations (str, Mandatory): Name of area
            number_of_days (int, Mandatory): Name of area
            person (int, Mandatory): Name of area
        """
        path = f"/{_id}/"
        data = {
            "alert_type": {
                "name": name,
                "description": description,
                "high_threshold": high_threshold,
                "medium_threshold": medium_threshold,
                "low_threshold": low_threshold,
                "reverse": reverse,
                "category": category,
                "category_type_key": category_type_key,
                "action_suggestion": action_suggestion,
                "relevant_data": relevant_data,
                "action_suggestion_link": action_suggestion_link,
                "action_suggestion_name": action_suggestion_name,
                "action_suggestion_description": action_suggestion_description,
                "action_suggestion_flow_type": action_suggestion_flow_type,
            },
            "alert_type_classification_count": alert_type_classification_count,
            "classification": classification,
            "start_date": start_date.strftime(DATE_FORMAT),
            "end_date": end_date.strftime(DATE_FORMAT) if end_date else end_date,
            "notified": notified,
            "value": value,
            "person": person_id,
        }
        parameters = {
            "search": search,
            "alert_type": alert_type,
            "classification": classification_param,
            "alert_type_active": alert_type_active,
            "active": active,
            "only_last_update": only_last_update,
            "alert_category": alert_category,
        }
        return self._base_requests.put(path=path, data=data, parameters=parameters)

    def delete_alert(
        self,
        _id: int,
        search: str = None,
        alert_type: str = None,
        classification: str = None,
        alert_type_active: str = None,
        active: str = None,
        only_last_update: str = None,
        alert_category: str = None,
    ) -> dict:
        """Delete alert
        Reference:
            https://full.mindsight.com.br/stone/api/v1/docs/#tag/Afastamentos/operation/destroyAbsence

        Args:
            _id (int, Mandatory): Id of area to retrieve
            created__gt (datetime, Optional): Datetime to apply filter ">=" on created dates.
                Format "%Y-%m-%d %H:%M:%S"
            created__lt (datetime, Optional): Datetime to apply filter "<=" on created dates.
                Format "%Y-%m-%d %H:%M:%S"
            modified__gt (datetime, Optional): Datetime to apply filter ">=" on modified dates.
                Format "%Y-%m-%d %H:%M:%S"
            modified__lt (datetime, Optional): Datetime to apply filter "<=" on modified dates.
                Format "%Y-%m-%d %H:%M:%S"
        """
        path = f"/{_id}"

        parameters = {
            "search": search,
            "alert_type": alert_type,
            "classification": classification,
            "alert_type_active": alert_type_active,
            "active": active,
            "only_last_update": only_last_update,
            "alert_category": alert_category,
        }
        return self._base_requests.delete(
            path=path,
            parameters=parameters,
        )

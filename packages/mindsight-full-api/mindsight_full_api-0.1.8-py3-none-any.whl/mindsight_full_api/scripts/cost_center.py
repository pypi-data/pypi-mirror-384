"""This module provide methods to work with areas entity"""

from datetime import date
from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from mindsight_full_api.settings import (
    API_ENDPOINT_COST_CENTERS,
    API_ENDPOINT_PEOPLE,
    DATE_FORMAT,
)
from mindsight_full_api.utils.aux_functions import generate_url


class CostCenters(ApiEndpoint):
    """
    This class abstract the cost center endpoint methods
    """

    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_COST_CENTERS)

    def get_list_cost_centers(
        self,
        search: str = None,
    ) -> ApiPaginationResponse:
        """
        Get companies data

        Args:
            search (str, Optional): Datetime to apply filter ">=" on created dates.
            }
        """

        path = ""
        parameters = {
            "search": search,
            "page_size": self.page_size,
        }
        return ApiPaginationResponse(
            **self._base_requests.get(path=path, parameters=parameters).json(),
            headers=self._base_requests.headers,
        )

    def post_create_cost_center(
        self,
        name: str,
        start_date: date,
        person_id: int,
        end_date: date = None,
        code: str = None,
    ):
        """
        Create new cost center
        Args:
            start_date (date, Mandatory):
            name (str, Mandatory): The cost center name
            person_id (int, Mandatory): The start date of the person in this cost center
            end_date (date, Optional): The end date of the person in this cost center
            code (str, Mandatory): The cost center code
        """
        path = ""
        data = {
            "name": name,
            "start_date": start_date.strftime(DATE_FORMAT),
            "end_date": end_date.strftime(DATE_FORMAT) if end_date else end_date,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
            "code": code,
        }
        return self._base_requests.post(path=path, json=data)

    def get_cost_center(
        self,
        _id: int,
        search: str = None,
    ) -> dict:
        """
        Get retrieve cost center
        Args:
            _id (int, Mandatory): Id of area to retrieve
            search (str, Optional): Datetime to apply filter ">=" on created dates.
        """
        path = f"/{_id}"
        parameters = {
            "search": search,
        }
        return self._base_requests.get(
            path=path,
            parameters=parameters,
        )

    def get_cost_center_centers(
        self,
    ) -> dict:
        """
        Get retrieve cost centers dimension
        Args:
            _id (int, Mandatory): Id of area to retrieve
            search (str, Optional): Datetime to apply filter ">=" on created dates.
        """
        path = f"/get_centers"
        return self._base_requests.get(
            path=path,
        )

    def patch_edit_cost_center(
        self,
        _id: int,
        name: str,
        start_date: date,
        person_id: int,
        code: str = None,
        end_date: date = None,
        search: str = None,
    ) -> dict:
        """
        Edit cost center record

        Args:
            start_date (date, Mandatory):
            name (str, Mandatory): The cost center name
            person_id (int, Mandatory): The start date of the person in this cost center
            end_date (date, Optional): The end date of the person in this cost center
            code (str, Mandatory): The cost center code
        """
        path = f"/{_id}"
        data = {
            "name": name,
            "start_date": start_date.strftime(DATE_FORMAT),
            "end_date": end_date.strftime(DATE_FORMAT) if end_date else end_date,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
            "code": code,
        }
        parameters = {
            "search": search,
        }
        return self._base_requests.patch(path=path, json=data, parameters=parameters)

    def put_edit_cost_center(
        self,
        _id: int,
        name: str,
        start_date: date,
        person_id: int,
        code: str = None,
        end_date: date = None,
        search: str = None,
    ) -> dict:
        """
        Edit cost center record
        Args:
            start_date (date, Mandatory):
            name (str, Mandatory): The cost center name
            person_id (int, Mandatory): The start date of the person in this cost center
            end_date (date, Optional): The end date of the person in this cost center
            code (str, Mandatory): The cost center code
        """
        path = f"/{_id}"
        data = {
            "name": name,
            "start_date": start_date.strftime(DATE_FORMAT),
            "end_date": end_date.strftime(DATE_FORMAT) if end_date else end_date,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
            "code": code,
        }
        parameters = {
            "search": search,
        }
        return self._base_requests.put(path=path, json=data, parameters=parameters)

    def delete_cost_center(
        self,
        _id: int,
        search: str = None,
    ) -> dict:
        """
        Delete cost center record

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
        }
        return self._base_requests.delete(
            path=path,
            parameters=parameters,
        )

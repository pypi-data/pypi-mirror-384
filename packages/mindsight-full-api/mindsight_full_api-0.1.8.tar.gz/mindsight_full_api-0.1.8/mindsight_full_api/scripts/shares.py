"""This module provide methods to work with areas entity"""

from datetime import date
from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from mindsight_full_api.settings import (
    API_ENDPOINT_SHARES,
    API_ENDPOINT_PEOPLE,
    DATE_FORMAT,
)
from mindsight_full_api.utils.aux_functions import generate_url


class Shares(ApiEndpoint):
    """This class abstract the shares endpoint methods
    """

    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_SHARES)

    def get_list_shares(
        self,
    ) -> ApiPaginationResponse:
        """
        Create shares records
        Args:
        """
        path = ""
        parameters={
            "page_size":self.page_size
        }
        return ApiPaginationResponse(
            **self._base_requests.get(path=path, parameters=parameters),
            headers=self._base_requests.headers,
        )

    def post_create_shares(
        self,
        person_id: int,
        quantity: int = None,
        date: date = None,
        vesting_date: date = None,
        shares_type: str = None,
    ):
        """
        Create Shares record
        Args:
            date (date, Mandatory):
            amount (float, Mandatory):
            person_id (int, Mandatory):
            reference_date (date, Optional):
            reference_label(str, Optional):
            type (str, Optional):
        """
        path = ""
        data = {
            "quantity": quantity,
            "date": date.strftime(DATE_FORMAT),
            "vesting_date": vesting_date,
            "shares_type": shares_type,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
        }

        return self._base_requests.post(path=path, json=data)

    def get_shares(
        self,
        _id: int,
    ) -> dict:
        """
        Get Shares record
        Args:
            _id (int, Mandatory): Id of Shares record to retrieve
        """
        path = f"/{_id}"
        return self._base_requests.get(
            path=path,
        )

    def patch_edit_shares(
        self,
        _id: int,
        person_id: int,
        quantity: int = None,
        date: date = None,
        vesting_date: date = None,
        shares_type: str = None,
    ) -> dict:
        """
        Update Shares record
        Args:
            _id (int, Mandatory): The Shares record id to update
        """

        path = f"/{_id}"
        data = {
            "quantity": quantity,
            "date": date.strftime(DATE_FORMAT),
            "vesting_date": vesting_date,
            "shares_type": shares_type,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
        }
        return self._base_requests.patch(path=path, json=data)

    def put_edit_shares(
        self,
        _id: int,
        person_id: int,
        quantity: int = None,
        date: date = None,
        vesting_date: date = None,
        shares_type: str = None,
    ) -> dict:
        """
        Update Shares record
        Args:
            _id (int, Mandatory): The Shares record id to update

        """
        path = f"/{_id}"
        data = {
            "quantity": quantity,
            "date": date.strftime(DATE_FORMAT),
            "vesting_date": vesting_date,
            "shares_type": shares_type,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
        }
        return self._base_requests.put(path=path, json=data)

    def delete_shares(
        self,
        _id: int,
    ) -> dict:
        """
        Delete Shares record
        Args:
            _id (int, Mandatory): The Shares record id to delete
        """
        path = f"/{_id}"
        return self._base_requests.delete(
            path=path,
        )

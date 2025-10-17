"""This module provide methods to work with areas entity"""
from datetime import date
from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from mindsight_full_api.settings import (
    API_ENDPOINT_SHARES_VALUE,
    DATE_FORMAT,
)


class SharesValue(ApiEndpoint):
    """This class abstract the shares endpoint methods
    """

    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_SHARES_VALUE)

    def get_list_shares_value(
        self,
    ) -> ApiPaginationResponse:
        """
        Get list shares value records
        """
        path = ""
        parameters={
            "page_size":self.page_size
        }
        return ApiPaginationResponse(
            **self._base_requests.get(path=path, parameters=parameters).json(),
            
            headers=self._base_requests.headers,
        )

    def post_create_shares_value(
        self,
        value: float,
        date: date,
        shares_type: str,
    ):
        """
        Create shares value record
        Args:
            value (float, Mandatory):
            date (str, Mandatory):
            shares_type (str, Mandatory):
        """
        path = ""
        data = {
            "value": value,
            "date": date.strftime(DATE_FORMAT),
            "shares_type": shares_type,
        }

        return self._base_requests.post(path=path, json=data)

    def get_shares_value(
        self,
        _id: int,
    ) -> dict:
        """
        Get shares value record
        Args:
            _id (int, Mandatory): Id of shares value record to retrieve
        """
        path = f"/{_id}"
        return self._base_requests.get(
            path=path,
        )

    def patch_edit_shares_value(
        self,
        _id: int,
        value: float,
        date: date,
        shares_type: str,
    ) -> dict:
        """
        Update shares value record
        Args:
            _id (int, Mandatory): The shares value record id to update
        """

        path = f"/{_id}"
        data = {
            "value": value,
            "date": date.strftime(DATE_FORMAT),
            "shares_type": shares_type,
        }
        return self._base_requests.patch(path=path, json=data)

    def put_edit_shares_value(
        self,
        _id: int,
        value: float,
        date: date,
        shares_type: str,
    ) -> dict:
        """
        Update shares value record
        Args:
            _id (int, Mandatory): The shares value record id to update

        """
        path = f"/{_id}"
        data = {
            "value": value,
            "date": date.strftime(DATE_FORMAT),
            "shares_type": shares_type,
        }
        return self._base_requests.put(path=path, json=data)

    def delete_shares_value(
        self,
        _id: int,
    ) -> dict:
        """
        Delete shares value record
        Args:
            _id (int, Mandatory): The Shares record id to delete
        """
        path = f"/{_id}"
        return self._base_requests.delete(
            path=path,
        )

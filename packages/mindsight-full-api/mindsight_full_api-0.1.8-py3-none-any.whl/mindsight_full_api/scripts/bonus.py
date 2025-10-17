"""This module provide methods to work with areas entity"""

from datetime import date, datetime
from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from mindsight_full_api.settings import (
    API_ENDPOINT_BONUSES,
    API_ENDPOINT_PEOPLE,
    DATE_FORMAT,
    DATETIME_FORMAT,
)
from mindsight_full_api.utils.aux_functions import generate_url


class Bonus(ApiEndpoint):
    """This class abstract the bonus endpoint methods
    """

    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_BONUSES)

    def get_list_bonuses(
        self,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> ApiPaginationResponse:
        """
        Create bonus records
        Args:
            created__gt (datetime, Optional): Datetime to apply filter ">=" on created dates.
                Format "%Y-%m-%d %H:%M:%S"
            created__lt (datetime, Optional): Datetime to apply filter "<=" on created dates.
                Format "%Y-%m-%d %H:%M:%S"
            modified__gt (datetime, Optional): Datetime to apply filter ">=" on modified dates.
                Format "%Y-%m-%d %H:%M:%S"
            modified__lt (datetime, Optional): Datetime to apply filter "<=" on modified dates.
                Format "%Y-%m-%d %H:%M:%S"
            }
        """

        path = ""
        parameters = {
            "created__gt": created__gt.strftime(DATETIME_FORMAT)
            if created__gt
            else None,
            "created__lt": created__lt.strftime(DATETIME_FORMAT)
            if created__lt
            else None,
            "modified__gt": modified__gt.strftime(DATETIME_FORMAT)
            if modified__gt
            else None,
            "modified__lt": modified__lt.strftime(DATETIME_FORMAT)
            if modified__lt
            else None,
            "page_size": self.page_size,
        }
        return ApiPaginationResponse(
            **self._base_requests.get(path=path, parameters=parameters).json(),
            headers=self._base_requests.headers,
        )

    def post_create_bonus(
        self,
        date: date,
        amount: int,
        person_id: int,
        reference_date: date = None,
        reference_label: date = None,
        type: str = None,
    ):
        """
        Create bonus record
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
            "date": date.strftime(DATE_FORMAT),
            "reference_date": reference_date.strftime(DATE_FORMAT) if date else date,
            "reference_label": reference_label,
            "amount": amount,
            "type": type,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
        }

        return self._base_requests.post(path=path, json=data)

    def get_bonus(
        self,
        _id: int,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """
        Get bonus record
        Args:
            _id (int, Mandatory): Id of bonus record to retrieve
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
            "created__gt": created__gt.strftime(DATETIME_FORMAT)
            if created__gt
            else None,
            "created__lt": created__lt.strftime(DATETIME_FORMAT)
            if created__lt
            else None,
            "modified__gt": modified__gt.strftime(DATETIME_FORMAT)
            if modified__gt
            else None,
            "modified__lt": modified__lt.strftime(DATETIME_FORMAT)
            if modified__lt
            else None,
        }
        return self._base_requests.get(
            path=path,
            parameters=parameters,
        )

    def patch_edit_bonus(
        self,
        _id: int,
        date: date,
        amount: int,
        person_id: int,
        reference_date: date = None,
        reference_label: date = None,
        type: str = None,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """
        Update bonus record
        Args:
            _id (int, Mandatory): The bonus record id to update
            date (date, Mandatory):
            amount (float, Mandatory):
            person_id (int, Mandatory):
            reference_date (date, Optional):
            reference_label(str, Optional):
            type (str, Optional):
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
        data = {
            "date": date.strftime(DATE_FORMAT),
            "reference_date": reference_date.strftime(DATE_FORMAT) if date else date,
            "reference_label": reference_label,
            "amount": amount,
            "type": type,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
        }
        parameters = {
            "created__gt": created__gt.strftime(DATETIME_FORMAT)
            if created__gt
            else None,
            "created__lt": created__lt.strftime(DATETIME_FORMAT)
            if created__lt
            else None,
            "modified__gt": modified__gt.strftime(DATETIME_FORMAT)
            if modified__gt
            else None,
            "modified__lt": modified__lt.strftime(DATETIME_FORMAT)
            if modified__lt
            else None,
        }
        return self._base_requests.patch(path=path, json=data, parameters=parameters)

    def put_edit_bonus(
        self,
        _id: int,
        date: date,
        amount: int,
        person_id: int,
        reference_date: date = None,
        reference_label: date = None,
        type: str = None,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """
        Update bonus record
        Args:
            _id (int, Mandatory): The bonus record id to update
            date (date, Mandatory):
            amount (float, Mandatory):
            person_id (int, Mandatory):
            reference_date (date, Optional):
            reference_label(str, Optional):
            type (str, Optional):
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
        data = {
            "date": date.strftime(DATE_FORMAT),
            "reference_date": reference_date.strftime(DATE_FORMAT) if date else date,
            "reference_label": reference_label,
            "amount": amount,
            "type": type,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
        }
        parameters = {
            "created__gt": created__gt.strftime(DATETIME_FORMAT)
            if created__gt
            else None,
            "created__lt": created__lt.strftime(DATETIME_FORMAT)
            if created__lt
            else None,
            "modified__gt": modified__gt.strftime(DATETIME_FORMAT)
            if modified__gt
            else None,
            "modified__lt": modified__lt.strftime(DATETIME_FORMAT)
            if modified__lt
            else None,
        }
        return self._base_requests.put(path=path, json=data, parameters=parameters)

    def delete_bonus(
        self,
        _id: int,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """
        Delete bonus record
        Args:
            _id (int, Mandatory): The bonus record id to delete
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
            "created__gt": created__gt.strftime(DATETIME_FORMAT)
            if created__gt
            else None,
            "created__lt": created__lt.strftime(DATETIME_FORMAT)
            if created__lt
            else None,
            "modified__gt": modified__gt.strftime(DATETIME_FORMAT)
            if modified__gt
            else None,
            "modified__lt": modified__lt.strftime(DATETIME_FORMAT)
            if modified__lt
            else None,
        }
        return self._base_requests.delete(
            path=path,
            parameters=parameters,
        )

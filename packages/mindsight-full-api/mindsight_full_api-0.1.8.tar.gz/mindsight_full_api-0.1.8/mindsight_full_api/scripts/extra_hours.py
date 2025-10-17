"""This module provide methods to work with extra hours entity"""

from datetime import date, datetime
from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from mindsight_full_api.settings import (
    API_ENDPOINT_EXTRA_HOURS,
    API_ENDPOINT_PEOPLE,
    DATE_FORMAT,
    DATETIME_FORMAT,
)
from mindsight_full_api.utils.aux_functions import generate_url


class ExtraHours(ApiEndpoint):
    """
    This class abstract the extra hours endpoint methods
    """

    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_EXTRA_HOURS)

    def get_list_extra_hours(
        self,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> ApiPaginationResponse:
        """
        Get extra hours records
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

    def get_extra_hours(
        self,
        _id: int,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """
        Get extra hours record
        Args:
            _id (int, Mandatory): Id of extra hours record to retrieve
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
            "page_size":self.page_size
        }
        return self._base_requests.get(
            path=path,
            parameters=parameters,
        )

    def post_create_extra_hours(
        self,
        date: date,
        hours: float,
        amount: float,
        person_id: int,
        type: str = None,
    ):
        """Create new extra hours
        Reference:
        Args:
            date (date, Optional): Extra hours end date
            hours (float, Mandatory): Total extra hours worked
            amount (float, Mandatory): Total amount paid
            person_id (int, Mandatory): Id of person related
            type (str, Mandatory): The extra hours type
        """
        path = ""
        data = {
            "date": date.strftime(DATE_FORMAT),
            "hours": hours,
            "amount": amount,
            "type": type,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
        }
        return self._base_requests.post(path=path, json=data)

    def patch_edit_extra_hours(
        self,
        _id: int,
        date: date,
        hours: float,
        amount: float,
        person_id: int,
        type: str = None,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """
        Update extra hours record
        Args:
            _id (int, Mandatory): Extra hours record id
            date (date, Optional): Extra hours end date
            hours (float, Mandatory): Total extra hours worked
            amount (float, Mandatory): Total amount paid
            person_id (int, Mandatory): Id of person related
            type (str, Mandatory): The extra hours type
        """
        path = f"/{_id}"
        data = {
            "date": date.strftime(DATE_FORMAT),
            "hours": hours,
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

    def put_edit_extra_hours(
        self,
        _id: int,
        date: date,
        hours: float,
        amount: float,
        person_id: int,
        type: str = None,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """
        Update extra hours record
        Args:
            _id (int, Mandatory): Extra hours record id
            date (date, Optional): Extra hours end date
            hours (float, Mandatory): Total extra hours worked
            amount (float, Mandatory): Total amount paid
            person_id (int, Mandatory): Id of person related
            type (str, Mandatory): The extra hours type
        """
        path = f"/{_id}"
        data = {
            "date": date.strftime(DATE_FORMAT),
            "hours": hours,
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

    def delete_extra_hours(
        self,
        _id: int,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """
        Delete extra hours record
        Args:
            _id (int, Mandatory): Id extra hours record to delete
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

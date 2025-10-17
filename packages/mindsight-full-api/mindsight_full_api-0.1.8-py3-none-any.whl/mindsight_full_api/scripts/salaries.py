"""This module provide methods to work with salary entity"""

from datetime import date, datetime
from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from typing import Literal
from mindsight_full_api.settings import (
    API_ENDPOINT_SALARIES,
    API_ENDPOINT_RAISE_TYPES,
    API_ENDPOINT_PEOPLE,
    DATE_FORMAT,
    DATETIME_FORMAT,
)
from mindsight_full_api.utils.aux_functions import generate_url


class Salary(ApiEndpoint):
    """
    This class abstract the salary endpoint methods
    """

    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_SALARIES)

    def get_list_salary(
        self,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> ApiPaginationResponse:
        """Get salary list data
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

    def get_salary(
        self,
        _id: int,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """
        Get retrieve salary
        Reference:
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

    def post_create_salary(
        self,
        date: date,
        salary: float,
        person_id: int,
        salary_currency: str,
        raise_type_id: int,
        raise_type_old: Literal[
            "initial",
            "raise",
            "mandatory",
            "others",
        ]=None,
    ):
        """
        Create new salary
        Reference:

        Args:
            date (date, mandatory):
            salary (float, mandatory):
            person_id (int, mandatory):
            raise_type_old (date, mandatory):
            raise_type_id (int, mandatory):
        """
        path = ""
        data = {
            "date": date.strftime(DATE_FORMAT),
            "salary": salary,
            "raise_type_old": raise_type_old,
            "salary_currency": salary_currency,
            "raise_type": generate_url(
                base_path=API_ENDPOINT_RAISE_TYPES, path=f"/{raise_type_id}"
            ),
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
        }
        return self._base_requests.post(path=path, json=data)

    def patch_edit_salary(
        self,
        _id: int,
        date: date,
        salary: float,
        person_id: int,
        salary_currency: str,
        raise_type_id: int,
        raise_type_old: Literal[
            "initial",
            "raise",
            "mandatory",
            "others",
        ]=  None,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """
        Update salary record
        Args:
            _id (int, Mandatory): Salary record id
            date (date, mandatory):
            salary (float, mandatory):
            person_id (int, mandatory):
            raise_type_old (date, mandatory):
            raise_type_id (int, mandatory):
        """
        path = f"/{_id}"
        data = {
            "date": date.strftime(DATE_FORMAT),
            "salary": salary,
            "raise_type_old": raise_type_old,
            "salary_currency": salary_currency,
            "raise_type": generate_url(
                base_path=API_ENDPOINT_RAISE_TYPES, path=f"/{raise_type_id}"
            ),
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

    def put_edit_salary(
        self,
        _id: int,
        date: date,
        salary: float,
        person_id: int,
        salary_currency: str,
        raise_type_id: int,
        raise_type_old: Literal[
            "initial",
            "raise",
            "mandatory",
            "others",
        ]=  None,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """
        Update salary record
        Args:
            _id (int, Mandatory): Salary record id
            date (date, mandatory):
            salary (float, mandatory):
            person_id (int, mandatory):
            raise_type_old (date, mandatory):
            raise_type_id (int, mandatory):
        """
        path = f"/{_id}"
        data = {
            "date": date.strftime(DATE_FORMAT),
            "salary": salary,
            "raise_type_old": raise_type_old,
            "salary_currency": salary_currency,
            "raise_type": generate_url(
                base_path=API_ENDPOINT_RAISE_TYPES, path=f"/{raise_type_id}"
            ),
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

    def delete_salary(
        self,
        _id: int,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """
        Delete salary record
        Reference:
        Args:
            _id (int, Mandatory): Id of salary to retrieve
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

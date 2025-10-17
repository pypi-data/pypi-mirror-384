"""This module provide methods to work with areas entity"""

from datetime import date, datetime
from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from typing import Literal
from mindsight_full_api.settings import (
    API_ENDPOINT_VARIABLE_SALARIES,
    API_ENDPOINT_PEOPLE,
    API_ENDPOINT_RAISE_TYPES,
    DATE_FORMAT,
    DATETIME_FORMAT,
)
from mindsight_full_api.utils.aux_functions import generate_url


class VaraibleSalary(ApiEndpoint):
    """This class abstract the salary endpoint methods
    Reference:
    """

    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_VARIABLE_SALARIES)

    def get_list_variable_salary(
        self,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> ApiPaginationResponse:
        """Get variable salary list data
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

    def get_variable_salary(
        self,
        _id: int,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """Get retrieve variable salary
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

    def post_create_variable_salary(
        self,
        date: date,
        variable_salary: float,
        person_id: int,
        variable_salary_currency: str = None,
        reference_value: float = None,
        reference_value_currency: str = None,
        raise_type_id: int = None,
        value_achievement: int = None,
        raise_type_old: Literal[
            "initial",
            "raise",
            "mandatory",
            "others",
        ] = None,
    ):
        """Create new salary
        Reference:

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
            "date": date.strftime(DATE_FORMAT),
            "variable_salary": variable_salary,
            "variable_salary_currency": variable_salary_currency,
            "reference_value": reference_value,
            "reference_value_currency": reference_value_currency,
            "value_achievement": value_achievement,
            "raise_type": generate_url(
                base_path=API_ENDPOINT_RAISE_TYPES, path=f"/{raise_type_id}"
            )
            if raise_type_id
            else None,
            "raise_type_old": raise_type_old,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
        }
        return self._base_requests.post(path=path, json=data)

    def patch_edit_variable_salary(
        self,
        _id: int,
        date: date,
        variable_salary: float,
        person_id: int,
        variable_salary_currency: str = None,
        reference_value: float = None,
        reference_value_currency: str = None,
        raise_type_id: int = None,
        value_achievement: int = None,
        raise_type_old: Literal[
            "initial",
            "raise",
            "mandatory",
            "others",
        ] = None,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """
        Reference:
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
        path = f"/{_id}"
        data = {
            "date": date.strftime(DATE_FORMAT),
            "variable_salary": variable_salary,
            "variable_salary_currency": variable_salary_currency,
            "reference_value": reference_value,
            "reference_value_currency": reference_value_currency,
            "value_achievement": value_achievement,
            "raise_type": generate_url(
                base_path=API_ENDPOINT_RAISE_TYPES, path=f"/{raise_type_id}"
            )
            if raise_type_id
            else None,
            "raise_type_old": raise_type_old,
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

    def put_edit_variable_salary(
        self,
        _id: int,
        date: date,
        variable_salary: float,
        person_id: int,
        variable_salary_currency: str = None,
        reference_value: float = None,
        reference_value_currency: str = None,
        raise_type_id: int = None,
        value_achievement: int = None,
        raise_type_old: Literal[
            "initial",
            "raise",
            "mandatory",
            "others",
        ] = None,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """
        Reference:
            https://full.mindsight.com.br/stone/api/v1/docs/#tag/Afastamentos/operation/updatebonus

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
        path = f"/{_id}"
        data = {
            "date": date.strftime(DATE_FORMAT),
            "variable_salary": variable_salary,
            "variable_salary_currency": variable_salary_currency,
            "reference_value": reference_value,
            "reference_value_currency": reference_value_currency,
            "value_achievement": value_achievement,
            "raise_type": generate_url(
                base_path=API_ENDPOINT_RAISE_TYPES, path=f"/{raise_type_id}"
            )
            if raise_type_id
            else None,
            "raise_type_old": raise_type_old,
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

    def delete_variable_salary(
        self,
        _id: int,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """
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
        return self._base_requests.delete(
            path=path,
            parameters=parameters,
        )

"""This module provide methods to work with areas entity"""

from datetime import date, datetime
from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from typing import Literal
from mindsight_full_api.settings import (
    API_ENDPOINT_ABSENCES,
    API_ENDPOINT_PEOPLE,
    DATE_FORMAT,
    DATETIME_FORMAT,
)
from mindsight_full_api.utils.aux_functions import generate_url


class Absence(ApiEndpoint):
    """This class abstract the absence endpoint methods
    """

    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_ABSENCES)

    def get_list_absences(
        self,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> ApiPaginationResponse:
        """Get absence data
        https://full.mindsight.com.br/stone/api/v1/docs/#tag/Afastamentos/operation/listAbsences

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

    def post_create_absence(
        self,
        start_date: date,
        person_id: int,
        end_date: date = None,
        is_approved: bool = None,
        type: Literal[
            "assistance",
            "vacation",
            "vacation_work_days",
            "insurance",
            "sick_leave",
            "medical_leave",
            "sick_note",
            "maternity_leave",
            "others",
        ] = None,
        number_of_days: int = None,
        observations: str = None,
    ):
        """Create new absence
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
            "is_approved": is_approved,
            "type": type,
            "observations": observations,
            "number_of_days": number_of_days,
            "person": person_id,
        }

        return self._base_requests.post(path=path, json=data)

    def get_absence(
        self,
        _id: int,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """Get retrieve absence
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

    def patch_edit_absence(
        self,
        _id: int,
        start_date: date,
        person_id: int,
        end_date: date = None,
        is_approved: bool = None,
        type: str = None,
        observations: str = None,
        number_of_days: int = None,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """Edit area and last area record
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
            "start_date": start_date.strftime(DATE_FORMAT),
            "end_date": end_date.strftime(DATE_FORMAT) if end_date else end_date,
            "is_approved": is_approved,
            "type": type,
            "observations": observations,
            "number_of_days": number_of_days,
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

    def put_edit_absence(
        self,
        _id: int,
        start_date: date,
        person_id: int,
        end_date: date = None,
        is_approved: bool = None,
        type: str = None,
        observations: str = None,
        number_of_days: int = None,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """Edit absence

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
            "start_date": start_date.strftime(DATE_FORMAT),
            "end_date": end_date.strftime(DATE_FORMAT) if end_date else end_date,
            "is_approved": is_approved,
            "type": type,
            "observations": observations,
            "number_of_days": number_of_days,
            "person": person_id,
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

    def delete_absence(
        self,
        _id: int,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """Delete absence
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

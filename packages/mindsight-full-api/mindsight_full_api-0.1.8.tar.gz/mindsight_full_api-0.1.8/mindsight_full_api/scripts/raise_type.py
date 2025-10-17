"""This module provide methods to work with areas entity"""

from datetime import datetime
from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from typing import Literal
from mindsight_full_api.settings import (
    API_ENDPOINT_RAISE_TYPES,
    DATETIME_FORMAT,
)


class RaiseType(ApiEndpoint):
    """This class abstract the absence endpoint methods
    """

    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_RAISE_TYPES)

    def get_list_raise_type(
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

    def post_create_raise_type(
        self,
        key: str,
        description: str,
        description_pt_br: str = None,
        description_en: str = False,
        description_es: str = None,
        raise_type: Literal[
            "initial",
            "raise",
            "mandatory",
            "others",
        ] = None,
    ):
        """
        Args:
            start_date (date, Mandatory): Area start date
            end_date (date, Optional): Parent area id
            is_approved (bool, Mandatory): Code of area
            type (str, Mandatory): Name of area
            observations (str, Mandatory): Name of area
            number_of_days (int, Mandatory): Name of area
            person (int, Mandatory): Name of area
        """
        path = "/"
        data = {
            "key": key,
            "description": description,
            "description_pt_br": description_pt_br,
            "description_en": description_en,
            "description_es": description_es,
            "raise_type": raise_type,
        }

        return self._base_requests.post(path=path, data=data)

    def get_raise_type(
        self,
        _id: int,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """Get retrieve absence
        Reference:
            https://full.mindsight.com.br/stone/api/v1/docs/#tag/Afastamentos/operation/retrieveAbsence

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

    def patch_edit_raise_type(
        self,
        _id: int,
        key: str,
        description: str,
        description_pt_br: str = None,
        description_en: str = False,
        description_es: str = None,
        raise_type: Literal[
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
        """Edit area and last area record
        Reference:
            https://full.mindsight.com.br/stone/api/v1/docs/#tag/Afastamentos/operation/partialUpdateAbsence

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
            "key": key,
            "description": description,
            "description_pt_br": description_pt_br,
            "description_en": description_en,
            "description_es": description_es,
            "raise_type": raise_type,
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
        return self._base_requests.patch(path=path, data=data, parameters=parameters)

    def put_edit_raise_type(
        self,
        _id: int,
        key: str,
        description: str,
        description_pt_br: str = None,
        description_en: str = False,
        description_es: str = None,
        raise_type: Literal[
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
        """Edit absence
        Reference:
            https://full.mindsight.com.br/stone/api/v1/docs/#tag/Afastamentos/operation/updateAbsence

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
            "key": key,
            "description": description,
            "description_pt_br": description_pt_br,
            "description_en": description_en,
            "description_es": description_es,
            "raise_type": raise_type,
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
        return self._base_requests.put(path=path, data=data, parameters=parameters)

    def delete_raise_type(
        self,
        _id: int,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """
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

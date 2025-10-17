"""This module provide methods to work with areas entity"""

from datetime import date, datetime
from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from mindsight_full_api.settings import (
    API_ENDPOINT_POSITIONS,
    API_ENDPOINT_PEOPLE,
    DATE_FORMAT,
    DATETIME_FORMAT,
)
from mindsight_full_api.utils.aux_functions import generate_url


class Positions(ApiEndpoint):
    """This class abstract the position endpoint methods
    """

    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_POSITIONS)

    def get_positions(
        self,
        _id: int,
        search: str = None,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> ApiPaginationResponse:
        """
        get person position records
        Args:
            }
        """

        path = f"/{_id}"
        parameters = {
            "search": search,
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
        return self._base_requests.get(path=path, parameters=parameters, headers=self._base_requests.headers).json() 

    def get_list_positions(
        self,
        search: str = None,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> ApiPaginationResponse:
        """
        get position records
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
            "search": search,
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

    def post_create_position(
        self,
        start_date: date,
        name: str,
        person_id: int,
        end_date: date=None,
        uuid: str=None,
        name_pt_br: str=None,
        name_en: str=None,
        name_es: str=None,
        level: str=None,
        level_pt_br: str=None,
        level_en: str=None,
        level_es: str=None,
        level_order: int=None,
        seniority_level: str=None

    ):
        """
        Create person position record
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
            "name": name,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
            "start_date": start_date.strftime(DATE_FORMAT),
            "end_date": end_date.strftime(DATE_FORMAT) if end_date else end_date,
            "uuid": uuid,
            "name_pt_br": name_pt_br,
            "name_en": name_en,
            "name_es": name_es,
            "level": level,
            "level_pt_br": level_pt_br,
            "level_en": level_en,
            "level_es": level_es,
            "level_order": level_order,
            "seniority_level": seniority_level,
            
        }
        return self._base_requests.post(path=path, json=data)

    def put_edit_position(
        self,
        _id: int,
        start_date: date,
        name: str,
        person_id: int,
        end_date: date=None,
        uuid: str=None,
        name_pt_br: str=None,
        name_en: str=None,
        name_es: str=None,
        level: str=None,
        level_pt_br: str=None,
        level_en: str=None,
        level_es: str=None,
        level_order: int=None,
        seniority_level: str=None,
        search: str = None,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """
        Update person position record
        Args:
            _id (int, Mandatory): The person position record id to update
        """
        path = f"/{_id}"
        parameters = {
            "search": search,
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
        data = {
            "name": name,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
            "start_date": start_date.strftime(DATE_FORMAT),
            "end_date": end_date.strftime(DATE_FORMAT) if end_date else end_date,
            "uuid": uuid,
            "name_pt_br": name_pt_br,
            "name_en": name_en,
            "name_es": name_es,
            "level": level,
            "level_pt_br": level_pt_br,
            "level_en": level_en,
            "level_es": level_es,
            "level_order": level_order,
            "seniority_level": seniority_level,
            
        }
        return self._base_requests.put(path=path, json=data, parameters=parameters)
    
    def patch_edit_position(
        self,
        _id: int,
        start_date: date,
        name: str,
        person_id: int,
        end_date: date=None,
        uuid: str=None,
        name_pt_br: str=None,
        name_en: str=None,
        name_es: str=None,
        level: str=None,
        level_pt_br: str=None,
        level_en: str=None,
        level_es: str=None,
        level_order: int=None,
        seniority_level: str=None,
        search: str = None,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """
        Partial update person position record
        Args:
            _id (int, Mandatory): The person position record id to update
        """
        path = f"/{_id}"
        parameters = {
            "search": search,
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
        data = {
            "name": name,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
            "start_date": start_date.strftime(DATE_FORMAT),
            "end_date": end_date.strftime(DATE_FORMAT) if end_date else end_date,
            "uuid": uuid,
            "name_pt_br": name_pt_br,
            "name_en": name_en,
            "name_es": name_es,
            "level": level,
            "level_pt_br": level_pt_br,
            "level_en": level_en,
            "level_es": level_es,
            "level_order": level_order,
            "seniority_level": seniority_level,
            
        }
        return self._base_requests.patch(path=path, json=data, parameters=parameters)

    def delete_position(
        self,
        _id: int,
        search: str = None,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """
        Delete person position record
        Args:
            _id (int, Mandatory): The person position record id to delete
        """
        path = f"/{_id}"
        parameters = {
            "search": search,
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
            path=path, parameters=parameters
        )

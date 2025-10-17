"""This module provide methods to work with areas entity"""

from datetime import date, datetime
from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from mindsight_full_api.settings import (
    API_ENDPOINT_PEOPLE,
    API_ENDPOINT_PERFORMANCE_MISSIONS,
    DATE_FORMAT,
    DATETIME_FORMAT,
)
from mindsight_full_api.utils.aux_functions import generate_url


class PerformanceMissions(ApiEndpoint):
    """This class abstract the performance indicator endpoint methods
    """

    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_PERFORMANCE_MISSIONS)

    def get_list_performance_missions(
        self,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> ApiPaginationResponse:
        """Get performance missions data"""

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

    def post_create_performance_missions(
        self,
        date: date,
        description: str,
        result: str,
        person_id: int,
        mission_type: str = None,
        mission_class: str = None,
        weight: float = None,
        round: str = None,
        qualitative_score: str = None,
        description_pt_br: str = None,
        description_en: str = None,
        description_es: str = None,
        result_pt_br: str = None,
        result_en: str = None,
        result_es: str = None,
        target: str = None,
        target_pt_br: str = None,
        target_en: str = None,
        target_es: str = None,
        unit: str = None,
        reverse: bool = None,
    ):
        """Create new performance indicator"""
        path = ""
        data = {
            "date": date.strftime(DATE_FORMAT),
            "description": description,
            "result": result,
            "person_id": generate_url(API_ENDPOINT_PEOPLE, f"/{person_id}"),
            "mission_type": mission_type,
            "mission_class": mission_class,
            "weight": weight,
            "round": round,
            "qualitative_score": qualitative_score,
            "description_pt_br": description_pt_br,
            "description_en": description_en,
            "description_es": description_es,
            "result_pt_br": result_pt_br,
            "result_en": result_en,
            "result_es": result_es,
            "target": target,
            "target_pt_br": target_pt_br,
            "target_en": target_en,
            "target_es": target_es,
            "unit": unit,
            "reverse": reverse,
        }
        return self._base_requests.post(path=path, json=data)

    def get_performance_missions(
        self,
        _id: int,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """Get retrieve performance indicator
        Args:
            _id (int, Mandatory): Id of area to retrieve
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
            path=path, parameters=parameters
        )

    def patch_edit_performance_missions(
        self,
        _id: int,
        date: date,
        description: str,
        result: str,
        person_id: int,
        mission_type: str = None,
        mission_class: str = None,
        weight: float = None,
        round: str = None,
        qualitative_score: str = None,
        description_pt_br: str = None,
        description_en: str = None,
        description_es: str = None,
        result_pt_br: str = None,
        result_en: str = None,
        result_es: str = None,
        target: str = None,
        target_pt_br: str = None,
        target_en: str = None,
        target_es: str = None,
        unit: str = None,
        reverse: bool = None,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """Edit performance indicator record
        Args:
            _id (int, Mandatory): Area id
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
        data = {
            "date": date.strftime(DATE_FORMAT),
            "description": description,
            "result": result,
            "person_id": generate_url(API_ENDPOINT_PEOPLE, f"/{person_id}"),
            "mission_type": mission_type,
            "mission_class": mission_class,
            "weight": weight,
            "round": round,
            "qualitative_score": qualitative_score,
            "description_pt_br": description_pt_br,
            "description_en": description_en,
            "description_es": description_es,
            "result_pt_br": result_pt_br,
            "result_en": result_en,
            "result_es": result_es,
            "target": target,
            "target_pt_br": target_pt_br,
            "target_en": target_en,
            "target_es": target_es,
            "unit": unit,
            "reverse": reverse,
        }
        return self._base_requests.patch(path=path, parameters=parameters, json=data)

    def put_edit_performance_missions(
        self,
        _id: int,
        date: date,
        description: str,
        result: str,
        person_id: int,
        mission_type: str = None,
        mission_class: str = None,
        weight: float = None,
        round: str = None,
        qualitative_score: str = None,
        description_pt_br: str = None,
        description_en: str = None,
        description_es: str = None,
        result_pt_br: str = None,
        result_en: str = None,
        result_es: str = None,
        target: str = None,
        target_pt_br: str = None,
        target_en: str = None,
        target_es: str = None,
        unit: str = None,
        reverse: bool = None,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """Edit performance indicator record
        Args:
            _id (int, Mandatory): Area id
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
        data = {
            "date": date.strftime(DATE_FORMAT),
            "description": description,
            "result": result,
            "person_id": generate_url(API_ENDPOINT_PEOPLE, f"/{person_id}"),
            "mission_type": mission_type,
            "mission_class": mission_class,
            "weight": weight,
            "round": round,
            "qualitative_score": qualitative_score,
            "description_pt_br": description_pt_br,
            "description_en": description_en,
            "description_es": description_es,
            "result_pt_br": result_pt_br,
            "result_en": result_en,
            "result_es": result_es,
            "target": target,
            "target_pt_br": target_pt_br,
            "target_en": target_en,
            "target_es": target_es,
            "unit": unit,
            "reverse": reverse,
        }
        return self._base_requests.put(path=path, parameters=parameters, json=data)

    def delete_performance_missions(
        self,
        _id: int,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> dict:
        """Delete performance indicator record
        Args:
            _id (int, Mandatory): Id of area to retrieve
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
            path=path, parameters=parameters
        )

"""This module provide methods to work with areas entity"""

from datetime import date, datetime
from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from mindsight_full_api.settings import (
    API_ENDPOINT_PEOPLE,
    API_ENDPOINT_PERFORMANCE_INDICATORS,
    # API_ENDPOINT_PERFORMANCE_EVALUATIONS,
    # API_ENDPOINT_PERFORMANCE_LABELS,
    # API_ENDPOINT_PERFORMANCE_SECTIONS,
    DATE_FORMAT,
    DATETIME_FORMAT,
)
from mindsight_full_api.utils.aux_functions import generate_url


class PerformanceIndicators(ApiEndpoint):
    """This class abstract the performance indicator endpoint methods
    """

    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_PERFORMANCE_INDICATORS)

    def get_list_performance_indicators(
        self,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
    ) -> ApiPaginationResponse:
        """Get performance indicators data"""

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

    def post_create_performance_indicators(
        self,
        date: str,
        result: float,
        person_id: str,
        description: str = None,
        description_pt_br: str = None,
        description_en: str = None,
        description_es: str = None,
        target: float = None,
        unit: str = None,
        reverse: bool = None,
        round: str = None,
    ):
        """Create new performance indicator"""
        path = ""
        data = {
            "date": date.strftime(DATE_FORMAT),
            "result": result,
            "person_id": generate_url(API_ENDPOINT_PEOPLE, f"/{person_id}"),
            "description": description,
            "description_pt_br": description_pt_br,
            "description_en": description_en,
            "description_es": description_es,
            "target": target,
            "unit": unit,
            "reverse": reverse,
            "round": round,
        }
        return self._base_requests.post(path=path, json=data)

    def get_performance_indicators(
        self,
        _id: int,
    ) -> dict:
        """Get retrieve performance indicator
        Args:
            _id (int, Mandatory): Id of area to retrieve
        """
        path = f"/{_id}"
        return self._base_requests.get(
            path=path,
        )

    def patch_edit_performance_indicators(
        self,
        _id: int,
        date: str,
        result: float,
        person_id: str,
        description: str = None,
        description_pt_br: str = None,
        description_en: str = None,
        description_es: str = None,
        target: float = None,
        unit: str = None,
        reverse: bool = None,
        round: str = None,
    ) -> dict:
        """Edit performance indicator record
        Args:
            _id (int, Mandatory): Area id
        """
        path = f"/{_id}"
        data = {
            "date": date.strftime(DATE_FORMAT),
            "result": result,
            "person_id": generate_url(API_ENDPOINT_PEOPLE, f"/{person_id}"),
            "description": description,
            "description_pt_br": description_pt_br,
            "description_en": description_en,
            "description_es": description_es,
            "target": target,
            "unit": unit,
            "reverse": reverse,
            "round": round,
        }
        return self._base_requests.patch(path=path, json=data)

    def put_edit_performance_indicators(
        self,
        _id: int,
        date: str,
        result: float,
        person_id: str,
        description: str = None,
        description_pt_br: str = None,
        description_en: str = None,
        description_es: str = None,
        target: float = None,
        unit: str = None,
        reverse: bool = None,
        round: str = None,
    ) -> dict:
        """Edit performance indicator record
        Args:
            _id (int, Mandatory): Area id
        """
        path = f"/{_id}"
        data = {
            "date": date.strftime(DATE_FORMAT),
            "result": result,
            "person_id": generate_url(API_ENDPOINT_PEOPLE, f"/{person_id}"),
            "description": description,
            "description_pt_br": description_pt_br,
            "description_en": description_en,
            "description_es": description_es,
            "target": target,
            "unit": unit,
            "reverse": reverse,
            "round": round,
        }
        return self._base_requests.put(path=path, json=data)

    def delete_performance_indicators(
        self,
        _id: int,
    ) -> dict:
        """Delete performance indicator record
        Args:
            _id (int, Mandatory): Id of area to retrieve
        """
        path = f"/{_id}"
        return self._base_requests.delete(
            path=path,
        )

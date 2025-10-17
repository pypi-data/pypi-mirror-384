"""This module provide methods to work with areas entity"""

from datetime import date
from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from mindsight_full_api.settings import (
    API_ENDPOINT_PEOPLE,
    API_ENDPOINT_PERFORMANCE_EVALUATION_ROUNDS,
    API_ENDPOINT_PERFORMANCE_EVALUATIONS,
    API_ENDPOINT_PERFORMANCE_LABELS,
    API_ENDPOINT_PERFORMANCE_SECTIONS,
    DATE_FORMAT,
)
from mindsight_full_api.utils.aux_functions import generate_url


class PerformanceEvaluations(ApiEndpoint):
    """This class abstract the performance evaluation endpoint methods
    """

    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_PERFORMANCE_EVALUATIONS)

    def get_list_performance_evaluations(
        self,
    ) -> ApiPaginationResponse:
        """Get performance evaluation rounds data"""

        path = ""
        parameters = {
            "page_size": self.page_size,
        }
        return ApiPaginationResponse(
            **self._base_requests.get(path=path, parameters=parameters).json(),
            headers=self._base_requests.headers,
        )

    def post_create_performance_evaluations(
        self,
        score: float,
        person_id: id,
        date: date,
        section_id: int,
        label_id: int = None,
        round_id: int = None,
    ):
        """Create new performance evaluation"""
        path = ""
        data = {
            "score": score,
            "person_id": generate_url(API_ENDPOINT_PEOPLE, f"/{person_id}"),
            "date": date.strftime(DATE_FORMAT),
            "section": generate_url(
                API_ENDPOINT_PERFORMANCE_SECTIONS, f"/{section_id}"
            ),
            "label": generate_url(API_ENDPOINT_PERFORMANCE_LABELS, f"/{label_id}"),
            "round": generate_url(
                API_ENDPOINT_PERFORMANCE_EVALUATION_ROUNDS, f"/{round_id}"
            ),
        }
        return self._base_requests.post(path=path, json=data)

    def get_performance_evaluations(
        self,
        _id: int,
    ) -> dict:
        """Get retrieve performance evaluation
        Args:
            _id (int, Mandatory): Id of area to retrieve
        """
        path = f"/{_id}"
        return self._base_requests.get(
            path=path,
        )

    def patch_edit_performance_evaluations(
        self,
        _id: int,
        score: float,
        person_id: id,
        date: date,
        section_id: int,
        label_id: int = None,
        round_id: int = None,
    ) -> dict:
        """Edit performance evaluation round record
        Args:
            _id (int, Mandatory): Area id
        """
        path = f"/{_id}"
        data = {
            "score": score,
            "person_id": generate_url(API_ENDPOINT_PEOPLE, f"/{person_id}"),
            "date": date.strftime(DATE_FORMAT),
            "section": generate_url(
                API_ENDPOINT_PERFORMANCE_SECTIONS, f"/{section_id}"
            ),
            "label": generate_url(API_ENDPOINT_PERFORMANCE_LABELS, f"/{label_id}"),
            "round": generate_url(
                API_ENDPOINT_PERFORMANCE_EVALUATION_ROUNDS, f"/{round_id}"
            ),
        }
        return self._base_requests.patch(path=path, json=data)

    def put_edit_performance_evaluations(
        self,
        _id: int,
        score: float,
        person_id: id,
        date: date,
        section_id: int,
        label_id: int = None,
        round_id: int = None,
    ) -> dict:
        """Edit performance evaluation round record
        Args:
            _id (int, Mandatory): Area id
        """
        path = f"/{_id}"
        data = {
            "score": score,
            "person_id": generate_url(API_ENDPOINT_PEOPLE, f"/{person_id}"),
            "date": date.strftime(DATE_FORMAT),
            "section": generate_url(
                API_ENDPOINT_PERFORMANCE_SECTIONS, f"/{section_id}"
            ),
            "label": generate_url(API_ENDPOINT_PERFORMANCE_LABELS, f"/{label_id}"),
            "round": generate_url(
                API_ENDPOINT_PERFORMANCE_EVALUATION_ROUNDS, f"/{round_id}"
            ),
        }
        return self._base_requests.put(path=path, json=data)

    def delete_performance_evaluations(
        self,
        _id: int,
    ) -> dict:
        """Delete performance evaluation round record
        Args:
            _id (int, Mandatory): Id of area to retrieve
        """
        path = f"/{_id}"
        return self._base_requests.delete(
            path=path,
        )

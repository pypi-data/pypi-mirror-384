"""This module provide methods to work with areas entity"""

from datetime import date
from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from mindsight_full_api.settings import (
    API_ENDPOINT_PERFORMANCE_EVALUATION_ROUNDS,
    DATE_FORMAT,
)
from mindsight_full_api.utils.aux_functions import generate_url


class PerformanceEvaluationRounds(ApiEndpoint):
    """This class abstract the evaluation rounds endpoint methods
    """

    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_PERFORMANCE_EVALUATION_ROUNDS)

    def get_list_performance_evaluation_rounds(
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

    def post_create_performance_evaluation_rounds(
        self,
        name: str,
        date: date,
        name_pt_br: str = None,
        name_en: str = None,
        name_es: str = None,
        previous_round_id: str = None,
    ):
        """Create new performance evaluation round
        Args:
            name : (str, Mandatory)
            date (date, Mandatory)
            name_pt_br (str, Mandatory)
            name_en (str, Mandatory)
            name_es (str, Mandatory)
            previous_round (str, Mandatory)
        """
        path = ""
        data = {
            "name": name,
            "date": date.strftime(DATE_FORMAT),
            "name_pt_br": name_pt_br,
            "name_en": name_en,
            "name_es": name_es,
            "previous_round": generate_url(
                API_ENDPOINT_PERFORMANCE_EVALUATION_ROUNDS, f"/{previous_round_id}"
            ),
        }

        return self._base_requests.post(path=path, json=data)

    def get_performance_evaluation_rounds(
        self,
        _id: int,
    ) -> dict:
        """Get retrieve evaluation rounds
        Args:
            _id (int, Mandatory): Id of area to retrieve
        """
        path = f"/{_id}"
        return self._base_requests.get(
            path=path,
        )

    def patch_edit_performance_evaluation_rounds(
        self,
        _id: int,
        name: str,
        date: date,
        name_pt_br: str = None,
        name_en: str = None,
        name_es: str = None,
        previous_round_id: str = None,
    ) -> dict:
        """Edit performance evaluation round record
        Args:
            _id (int, Mandatory): Area id
        """
        path = f"/{_id}"
        data = {
            "name": name,
            "date": date.strftime(DATE_FORMAT),
            "name_pt_br": name_pt_br,
            "name_en": name_en,
            "name_es": name_es,
            "previous_round_id": generate_url(
                API_ENDPOINT_PERFORMANCE_EVALUATION_ROUNDS, f"/{previous_round_id}"
            ),
        }
        return self._base_requests.patch(path=path, json=data)

    def put_edit_performance_evaluation_rounds(
        self,
        _id: int,
        name: str,
        date: date,
        name_pt_br: str = None,
        name_en: str = None,
        name_es: str = None,
        previous_round_id: str = None,
    ) -> dict:
        """Edit performance evaluation round record
        Args:
            _id (int, Mandatory): Area id
        """
        path = f"/{_id}"
        data = {
            "name": name,
            "date": date.strftime(DATE_FORMAT),
            "name_pt_br": name_pt_br,
            "name_en": name_en,
            "name_es": name_es,
            "previous_round_id": generate_url(
                API_ENDPOINT_PERFORMANCE_EVALUATION_ROUNDS, f"/{previous_round_id}"
            ),
        }

        return self._base_requests.put(path=path, json=data)

    def delete_performance_evaluation_rounds(
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

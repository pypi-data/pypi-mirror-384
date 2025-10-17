"""This module provide methods to work with areas entity"""

from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from mindsight_full_api.settings import (
    API_ENDPOINT_PERFORMANCE_LABELS,
)


class PerformanceLabels(ApiEndpoint):
    """This class abstract the performance label endpoint methods
    """

    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_PERFORMANCE_LABELS)

    def get_list_performance_labels(
        self,
    ) -> ApiPaginationResponse:
        """Get performance labels data"""

        path = ""
        parameters = {
            "page_size": self.page_size,
        }
        return ApiPaginationResponse(
            **self._base_requests.get(path=path, parameters=parameters).json(),
            headers=self._base_requests.headers,
        )

    def post_create_performance_labels(
        self,
        key:str,
        score_description:str,
        color:str,
        color_comparative:str,
        scores:str,
    ):
        """Create new performance label"""
        path = ""
        data ={
            "key": key,
            "score_description": score_description,
            "color": color,
            "color_comparative": color_comparative,
            "scores": scores,
        }
        return self._base_requests.post(path=path, json=data)

    def get_performance_labels(
        self,
        _id: int,
    ) -> dict:
        """Get retrieve performance label
        Args:
            _id (int, Mandatory): Id of area to retrieve
        """
        path = f"/{_id}"
        return self._base_requests.get(
            path=path
        )

    def patch_edit_performance_labels(
        self,
        _id: int,
        key:str,
        score_description:str,
        color:str,
        color_comparative:str,
        scores:str,
    ) -> dict:
        """Edit performance label record
        Args:
            _id (int, Mandatory): Area id
        """
        path = f"/{_id}"
        data ={
            "key": key,
            "score_description": score_description,
            "color": color,
            "color_comparative": color_comparative,
            "scores": scores,
        }
        return self._base_requests.patch(path=path, json=data)

    def put_edit_performance_labels(
        self,
        _id: int,
        key:str,
        score_description:str,
        color:str,
        color_comparative:str,
        scores:str,
    ) -> dict:
        """Edit performance label record
        Args:
            _id (int, Mandatory): Area id
        """
        path = f"/{_id}"
        data ={
            "key": key,
            "score_description": score_description,
            "color": color,
            "color_comparative": color_comparative,
            "scores": scores,
        }
        return self._base_requests.put(path=path, json=data)

    def delete_performance_labels(
        self,
        _id: int,
    ) -> dict:
        """Delete performance label record
        Args:
            _id (int, Mandatory): Id of area to retrieve
        """
        path = f"/{_id}"
        return self._base_requests.delete(
            path=path,
        )

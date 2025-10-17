"""This module provide methods to work with areas entity"""

from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from mindsight_full_api.settings import (
    API_ENDPOINT_PERFORMANCE_SECTIONS,
)


class PerformanceSections(ApiEndpoint):
    """This class abstract the performance section endpoint methods
    """

    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_PERFORMANCE_SECTIONS)

    def get_list_performance_sections(
        self,
    ) -> ApiPaginationResponse:
        """Get performance sections data"""

        path = ""
        parameters = {
            "page_size": self.page_size,
        }
        return ApiPaginationResponse(
            **self._base_requests.get(path=path, parameters=parameters).json(),
            headers=self._base_requests.headers,
        )

    def post_create_performance_sections(
        self,
        name:str 
    ):
        """Create new performance section"""
        path = ""
        data ={
        "name": name
        }
        return self._base_requests.post(path=path, json=data)

    def get_performance_sections(
        self,
        _id: int,
    ) -> dict:
        """Get retrieve performance section
        Args:
            _id (int, Mandatory): Id of area to retrieve
        """
        path = f"/{_id}"
        return self._base_requests.get(
            path=path
        )

    def patch_edit_performance_sections(
        self,
        _id: int,
        name:str,
    ) -> dict:
        """Edit performance section record
        Args:
            _id (int, Mandatory): Area id
        """
        path = f"/{_id}"
        data ={
        "name":name
        }
        return self._base_requests.patch(path=path, json=data)

    def put_edit_performance_sections(
        self,
        _id: int,
        name:str,
    ) -> dict:
        """Edit performance section record
        Args:
            _id (int, Mandatory): Area id
        """
        path = f"/{_id}"
        data ={
        "name":name
        }
        return self._base_requests.put(path=path, json=data)

    def delete_performance_sections(
        self,
        _id: int,
    ) -> dict:
        """Delete performance section record
        Args:
            _id (int, Mandatory): Id of area to retrieve
        """
        path = f"/{_id}"
        return self._base_requests.delete(
            path=path,
        )

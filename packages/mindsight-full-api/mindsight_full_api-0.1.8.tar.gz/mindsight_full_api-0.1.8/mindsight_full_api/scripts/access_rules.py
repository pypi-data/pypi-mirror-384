"""This module provide methods to work with access rules entity"""

from typing import List, Literal, Optional

from requests import Response

from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from mindsight_full_api.settings import API_ENDPOINT_ACCESS_RULES, API_ENDPOINT_USERS
from mindsight_full_api.utils.aux_functions import generate_url

ACCESS_RULES_TYPES = Literal["fixed_filter", "dynamic_filter", "tree", "individual"]


class AccessRules(ApiEndpoint):
    """This class abstract the access rules endpoint methods"""

    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_ACCESS_RULES)

    def get_list_access_rules(
        self,
        type: ACCESS_RULES_TYPES,
        user: Optional[str] = None,
        person: Optional[str] = None,
    ) -> ApiPaginationResponse:
        """Get a list with the access rules"""
        path = ""
        parameters = {
            "page_size": self.page_size,
            "type": type,
            "user": user,
            "person": person,
        }
        return ApiPaginationResponse(
            **self._base_requests.get(path=path, parameters=parameters).json(),
            headers=self._base_requests.headers,
        )

    def post_create_access_rules(
        self,
        type: ACCESS_RULES_TYPES,
        owner: str,
        access_rule_users: List[str],
        access_rule_target: int,
    ) -> Response:
        """
        Creates an access rule to a user
        Args:
            type: the type of access rule to create
                Possible values are:
                - fixed_filter
                - dynamic_filter
                - tree
                - individual
            owner: the owner of the access rule, usually a user id
            access_rule_users: list of users ids to apply the access rule
            access_rule_target: the user id target of the access rule
        """
        path = ""
        data = {
            "owner": generate_url(
                base_path=API_ENDPOINT_USERS,
                path=f"/{owner}",
            ),
            "user": [
                generate_url(
                    base_path=API_ENDPOINT_USERS,
                    path=f"/{user}",
                )
                for user in access_rule_users
                if user
            ],
            "type": type,
            "params": {
                "person_id": access_rule_target,
            },
        }
        return self._base_requests.post(path=path, json=data)

    def get_access_rule(self, access_rule_id: str) -> Response:
        """Get a specific access rule by its ID"""
        path = f"/{access_rule_id}"
        return self._base_requests.get(path=path)

    def put_update_access_rule(
        self,
        access_rule_id: str,
        type: ACCESS_RULES_TYPES,
        owner: str,
        access_rule_users: List[str],
        access_rule_target: int,
    ) -> Response:
        """
        Updates an existing access rule
        Args:
            access_rule_id: the ID of the access rule to update
            type: the type of access rule to create
                Possible values are:
                - fixed_filter
                - dynamic_filter
                - tree
                - individual
            owner: the owner of the access rule, usually a user id
            access_rule_users: list of users ids to apply the access rule
            access_rule_target: the user id target of the access rule
        """
        path = f"/{access_rule_id}"
        data = {
            "owner": generate_url(
                base_path=API_ENDPOINT_USERS,
                path=f"/{owner}",
            ),
            "user": [
                generate_url(
                    base_path=API_ENDPOINT_USERS,
                    path=f"/{user}",
                )
                for user in access_rule_users
                if user
            ],
            "type": type,
            "params": {
                "person_id": access_rule_target,
            },
        }
        return self._base_requests.put(path=path, json=data)

    def delete_access_rule(self, access_rule_id: str) -> Response:
        """Delete an access rule by its ID"""
        path = f"/{access_rule_id}"
        return self._base_requests.delete(path=path)

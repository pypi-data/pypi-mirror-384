"""This module provide methods to work with areas entity"""

from datetime import date, datetime
from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from mindsight_full_api.settings import (
    API_ENDPOINT_USERS,
    API_ENDPOINT_PEOPLE,
    DATE_FORMAT,
    DATETIME_FORMAT,
)
from mindsight_full_api.utils.aux_functions import generate_url


class User(ApiEndpoint):
    """This class abstract the user endpoint methods
    """

    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_USERS)

    def get_list_users(
        self,
        search: str = None,
        remuneration_access: str = None,
        my_profile_remuneration_access: str = None,
        without_rule: str = None,
        is_active: str = None,
        ordering: str = None,
    ) -> ApiPaginationResponse:
        """
        Create user records
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
            "page_size": self.page_size,
            "search": search,
            "remuneration_access": remuneration_access,
            "my_profile_remuneration_access": my_profile_remuneration_access,
            "without_rule": without_rule,
            "is_active": is_active,
            "ordering": ordering,
        }
        return ApiPaginationResponse(
            **self._base_requests.get(path=path, parameters=parameters).json(),
            headers=self._base_requests.headers,
        )

    def post_create_user(
        self,
        username: str,
        password: str,
        email: str,
        first_name: str,
        last_name: str,
        groups: list[str],
        user_permissions: list[str],
        is_superuser: bool,
        is_active: bool,
    ):
        """
        Create user record
        Args:
            username: (str, Mandatory):
            password: (str, Mandatory):
            email: (str, Mandatory):
            first_name: (str, Mandatory):
            last_name: (str, Mandatory):
            groups: (list[str], Mandatory):
            user_permissions: (list[str], Mandatory):
            is_superuser: (bool, Mandatory):
            is_active:  (bool, Mandatory):
        """
        path = ""
        data = {
            "username": username,
            "password": password,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "groups": groups,
            "user_permissions": user_permissions,
            "is_superuser": is_superuser,
            "is_active": is_active,
        }
        return self._base_requests.post(path=path, json=data)

    def get_user(
        self,
        _id: int,
        search: str = None,
        remuneration_access: str = None,
        my_profile_remuneration_access: str = None,
        without_rule: str = None,
        is_active: str = None,
        ordering: str = None,
    ) -> dict:
        """
        Get user record
        Args:
            _id (int, Mandatory): Id of user record to retrieve
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
            "search": search,
            "remuneration_access": remuneration_access,
            "my_profile_remuneration_access": my_profile_remuneration_access,
            "without_rule": without_rule,
            "is_active": is_active,
            "ordering": ordering,
        }
        return self._base_requests.get(
            path=path,
            parameters=parameters,
        )

    def patch_edit_user(
        self,
        _id: int,
        username: str,
        notifications_config: str,
        email: str = None,
        first_name: str = None,
        last_name: str = None,
        groups: list[str] = None,
        user_permissions: list[str] = None,
        is_superuser: bool = None,
        last_login: datetime = None,
        date_joined: datetime = None,
        is_active: bool = None,
        last_acess: datetime = None,
        search: str = None,
        is_active_param: bool = None,
        remuneration_access: str = None,
        my_profile_remuneration_access: str = None,
        without_rule: str = None,
        ordering: str = None,
    ) -> dict:
        """
        Update user record
        Args:
            _id (int, Mandatory): The user record id to update
            username: (str, Mandatory)
            email: (str, Mandatory)
            notifications_config: (str, Mandatory)
            first_name: (str, Mandatory)
            last_name: (str, Mandatory)
            groups: (list[str], Mandatory)
            user_permissions: (list[str], Mandatory)
            is_superuser: (bool, Mandatory)
            is_active:  (bool, Mandatory)
        """

        path = f"/{_id}"
        data = {
            "username": username,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "groups": groups,
            "user_permissions": user_permissions,
            "is_superuser": is_superuser,
            "notifications_config": notifications_config,
            "last_login": last_login.strftime(DATETIME_FORMAT)
            if last_login
            else last_login,
            "date_joined": date_joined.strftime(DATETIME_FORMAT)
            if date_joined
            else date_joined,
            "is_active": is_active,
            "last_acess": last_acess.strftime(DATETIME_FORMAT)
            if last_acess
            else last_acess,
        }
        parameters = {
            "search": search,
            "remuneration_access": remuneration_access,
            "my_profile_remuneration_access": my_profile_remuneration_access,
            "without_rule": without_rule,
            "is_active": is_active_param,
            "ordering": ordering,
        }
        return self._base_requests.patch(path=path, json=data, parameters=parameters)

    def put_edit_user(
        self,
        _id: int,
        username: str,
        notifications_config: str,
        email: str = None,
        first_name: str = None,
        last_name: str = None,
        groups: list[str] = None,
        user_permissions: list[str] = None,
        is_superuser: bool = None,
        last_login: datetime = None,
        date_joined: datetime = None,
        is_active: bool = None,
        is_active_param: bool = None,
        last_acess: datetime = None,
        search: str = None,
        remuneration_access: str = None,
        my_profile_remuneration_access: str = None,
        without_rule: str = None,
        ordering: str = None,
    ) -> dict:
        """
        Update user record
        Args:
            _id (int, Mandatory): The user record id to update
            date (date, Mandatory):
            amount (float, Mandatory):
            person_id (int, Mandatory):
            reference_date (date, Optional):
            reference_label(str, Optional):
            type (str, Optional):
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
        data = {
            "username": username,
            "notifications_config": notifications_config,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "groups": groups,
            "user_permissions": user_permissions,
            "is_superuser": is_superuser,
            "last_login": last_login.strftime(DATETIME_FORMAT)
            if last_login
            else last_login,
            "date_joined": date_joined.strftime(DATETIME_FORMAT)
            if date_joined
            else date_joined,
            "is_active": is_active,
            "last_acess": last_acess.strftime(DATETIME_FORMAT)
            if last_acess
            else last_acess,
        }
        parameters = {
            "search": search,
            "remuneration_access": remuneration_access,
            "my_profile_remuneration_access": my_profile_remuneration_access,
            "without_rule": without_rule,
            "is_active": is_active_param,
            "ordering": ordering,
        }
        return self._base_requests.put(path=path, json=data, parameters=parameters)

    def delete_user(
        self,
        _id: int,
        search: str = None,
        remuneration_access: str = None,
        my_profile_remuneration_access: str = None,
        is_active: bool = None,
        without_rule: str = None,
        ordering: str = None,
    ) -> dict:
        """
        Delete user record
        Args:
            _id (int, Mandatory): The user record id to delete
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
            "search": search,
            "remuneration_access": remuneration_access,
            "my_profile_remuneration_access": my_profile_remuneration_access,
            "without_rule": without_rule,
            "is_active": is_active,
            "ordering": ordering,
        }
        return self._base_requests.delete(
            path=path,
            parameters=parameters,
        )

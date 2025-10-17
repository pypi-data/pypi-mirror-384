"""This module provide a base to use requests for api"""

from typing import Any, Literal

import requests

from mindsight_full_api.helpers.exceptions import (
    BadRequestException,
    ServerErrorException,
)
from mindsight_full_api.settings import API_TOKEN, TIMEOUT
from mindsight_full_api.utils.aux_functions import generate_url


class BaseRequests:
    """Aux class to communicate with mindsight api"""

    def __init__(self):
        self.__token = API_TOKEN
        self.headers = None
        self.base_path = "/"

    def __authorization_header(self) -> dict:
        return {
            "Authorization": f"Token {self.__token}",
            "Content-Type": "application/json",
        }

    def __check_response(self, response: requests.Response):
        content_text = response.text
        try:
            response.raise_for_status()

        except requests.HTTPError as http_error:

            if response.status_code == 400:
                raise BadRequestException(message=content_text) from http_error

            if response.status_code == 500:
                raise ServerErrorException(message=content_text) from http_error

            raise requests.HTTPError(http_error) from http_error

        except Exception as exc:
            raise exc

    def __request_helper(
        self,
        path: str,
        method: Literal["get", "post", "put", "patch", "delete"],
        headers: dict = None,
        parameters: dict = None,
        data: Any = None,
        json: Any = None,
    ):
        if not headers:
            headers = {}

        request_url = generate_url(base_path=self.base_path, path=path)
        self.headers = {**self.__authorization_header(), **headers}
        response = None
        method = method.lower()

        if method == "get":
            response = requests.get(
                url=request_url,
                headers=self.headers,
                params=parameters,
                data=data,
                timeout=TIMEOUT,
            )

        elif method == "post":
            response = requests.post(
                url=request_url,
                headers=self.headers,
                params=parameters,
                data=data,
                json=json,
                timeout=TIMEOUT,
            )

        elif method == "put":
            response = requests.put(
                url=request_url,
                headers=self.headers,
                params=parameters,
                data=data,
                json=json,
                timeout=TIMEOUT,
            )

        elif method == "patch":
            response = requests.patch(
                url=request_url,
                headers=self.headers,
                params=parameters,
                data=data,
                json=json,
                timeout=TIMEOUT,
            )

        elif method == "delete":
            response = requests.delete(
                url=request_url,
                headers=self.headers,
                params=parameters,
                data=data,
                json=json,
                timeout=TIMEOUT,
            )

        # Check response
        self.__check_response(response)
        if response.status_code == 204:
            return response
        return response

    def get(
        self,
        path: str,
        headers: dict = None,
        parameters: dict = None,
    ) -> Any:
        """Use GET method on Rest API"""
        return self.__request_helper(
            path=path, method="get", headers=headers, parameters=parameters
        )

    def post(
        self,
        path: str,
        headers: dict = None,
        parameters: dict = None,
        data: Any = None,
        json: Any = None,
    ) -> Any:
        """Use POST method on Rest API"""
        return self.__request_helper(
            path=path,
            method="post",
            headers=headers,
            parameters=parameters,
            data=data,
            json=json,
        )

    def put(
        self,
        path: str,
        headers: dict = None,
        parameters: dict = None,
        data: Any = None,
        json: Any = None,
    ):
        """Use PUT method on Rest API"""
        return self.__request_helper(
            path=path,
            method="put",
            headers=headers,
            parameters=parameters,
            data=data,
            json=json,
        )

    def patch(
        self,
        path: str,
        headers: dict = None,
        parameters: dict = None,
        data: Any = None,
        json: Any = None,
    ):
        """Use PATCH method on Rest API"""
        return self.__request_helper(
            path=path,
            method="patch",
            headers=headers,
            parameters=parameters,
            data=data,
            json=json,
        )

    def delete(
        self,
        path: str,
        headers: dict = None,
        parameters: dict = None,
        data: Any = None,
    ):
        """Use DELETE method on Rest API"""
        return self.__request_helper(
            path=path,
            method="delete",
            headers=headers,
            parameters=parameters,
            data=data,
        )

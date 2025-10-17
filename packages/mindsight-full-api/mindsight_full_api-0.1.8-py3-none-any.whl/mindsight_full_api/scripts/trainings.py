"""This module provide methods to work with areas entity"""

from datetime import date, datetime
from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from typing import Literal
from mindsight_full_api.settings import (
    API_ENDPOINT_TRAININGS,
    API_ENDPOINT_PEOPLE,
    DATE_FORMAT,
    DATETIME_FORMAT,
)
from mindsight_full_api.utils.aux_functions import generate_url


class Trainings(ApiEndpoint):
    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_TRAININGS)

    def get_list_training(
        self,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
        status: Literal[
            "pending",
            "pending_renovation",
            "in_progress",
            "concluded",
            "failed",
            "suspended",
            "canceled",
            "closed",
        ] = None,
    ) -> ApiPaginationResponse:
        """
        Get training data
        Args:
            created__gt (datetime, Optional): Datetime to apply filter ">=" on created dates.
                Format "%Y-%m-%d %H:%M:%S"
            created__lt (datetime, Optional): Datetime to apply filter "<=" on created dates.
                Format "%Y-%m-%d %H:%M:%S"
            modified__gt (datetime, Optional): Datetime to apply filter ">=" on modified dates.
                Format "%Y-%m-%d %H:%M:%S"
            modified__lt (datetime, Optional): Datetime to apply filter "<=" on modified dates.
                Format "%Y-%m-%d %H:%M:%S"
            status (str, Optional): The training status
        """
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
            "status": status,
        }
        return ApiPaginationResponse(
            **self._base_requests.get(path=path, parameters=parameters).json(),
            headers=self._base_requests.headers,
        )

    def post_create_training(
        self,
        date: datetime,
        course: str,
        person_id: id,
        course_pt_br: str = None,
        course_en: str = None,
        course_es: str = None,
        course_id: str = None,
        performance: str = None,
        performance_pt_br: str = None,
        performance_en: str = None,
        performance_es: str = None,
        old_status: Literal[
            "pending",
            "pending_renovation",
            "in_progress",
            "concluded",
            "failed",
            "suspended",
            "canceled",
            "closed",
        ] = None,
        status: Literal[
            "pending",
            "pending_renovation",
            "in_progress",
            "concluded",
            "failed",
            "suspended",
            "canceled",
            "closed",
        ] = None,
        mandatory: bool = None,
    ):
        """
        Post create training record
        """
        path = ""
        data = {
            "date": date.strftime(DATE_FORMAT),
            "course": course,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
            "course_pt_br": course_pt_br,
            "course_en": course_en,
            "course_es": course_es,
            "course_id": course_id,
            "performance": performance,
            "performance_pt_br": performance_pt_br,
            "performance_en": performance_en,
            "performance_es": performance_es,
            "old_status": old_status,
            "status": status,
            "mandatory": mandatory,
        }
        return self._base_requests.post(path=path, json=data)

    def get_training(
        self,
        _id: int,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
        status: Literal[
            "pending",
            "pending_renovation",
            "in_progress",
            "concluded",
            "failed",
            "suspended",
            "canceled",
            "closed",
        ] = None,
    ) -> dict:
        """
        Get training record
        Args:
            created__gt (datetime, Optional): Datetime to apply filter ">=" on created dates.
                Format "%Y-%m-%d %H:%M:%S"
            created__lt (datetime, Optional): Datetime to apply filter "<=" on created dates.
                Format "%Y-%m-%d %H:%M:%S"
            modified__gt (datetime, Optional): Datetime to apply filter ">=" on modified dates.
                Format "%Y-%m-%d %H:%M:%S"
            modified__lt (datetime, Optional): Datetime to apply filter "<=" on modified dates.
                Format "%Y-%m-%d %H:%M:%S"
            status (str, Optional): The training status
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
            "page_size": self.page_size,
            "status": status,
        }
        return self._base_requests.get(path=path, parameters=parameters)

    def patch_edit_training(
        self,
        _id: int,
        date: datetime,
        course: str,
        person_id: id,
        course_pt_br: str = None,
        course_en: str = None,
        course_es: str = None,
        course_id: str = None,
        performance: str = None,
        performance_pt_br: str = None,
        performance_en: str = None,
        performance_es: str = None,
        old_status: Literal[
            "pending",
            "pending_renovation",
            "in_progress",
            "concluded",
            "failed",
            "suspended",
            "canceled",
            "closed",
        ] = None,
        status: Literal[
            "pending",
            "pending_renovation",
            "in_progress",
            "concluded",
            "failed",
            "suspended",
            "canceled",
            "closed",
        ] = None,
        mandatory: bool = None,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
        status_param: Literal[
            "pending",
            "pending_renovation",
            "in_progress",
            "concluded",
            "failed",
            "suspended",
            "canceled",
            "closed",
        ] = None,
    ):
        """
        Partial Update training record
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
            "page_size": self.page_size,
            "status": status_param,
        }
        data = {
            "date": date.strftime(DATE_FORMAT),
            "course": course,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
            "course_pt_br": course_pt_br,
            "course_en": course_en,
            "course_es": course_es,
            "course_id": course_id,
            "performance": performance,
            "performance_pt_br": performance_pt_br,
            "performance_en": performance_en,
            "performance_es": performance_es,
            "old_status": old_status,
            "status": status,
            "mandatory": mandatory,
        }
        return self._base_requests.patch(path=path, json=data, parameters=parameters)

    def put_edit_training(
        self,
        _id: int,
        date: datetime,
        course: str,
        person_id: id,
        course_pt_br: str = None,
        course_en: str = None,
        course_es: str = None,
        course_id: str = None,
        performance: str = None,
        performance_pt_br: str = None,
        performance_en: str = None,
        performance_es: str = None,
        old_status: Literal[
            "pending",
            "pending_renovation",
            "in_progress",
            "concluded",
            "failed",
            "suspended",
            "canceled",
            "closed",
        ] = None,
        status: Literal[
            "pending",
            "pending_renovation",
            "in_progress",
            "concluded",
            "failed",
            "suspended",
            "canceled",
            "closed",
        ] = None,
        mandatory: bool = None,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
        status_param: Literal[
            "pending",
            "pending_renovation",
            "in_progress",
            "concluded",
            "failed",
            "suspended",
            "canceled",
            "closed",
        ] = None,
    ):
        """
        Update training record
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
            "page_size": self.page_size,
            "status": status_param,
        }
        data = {
            "date": date.strftime(DATE_FORMAT),
            "course": course,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
            "course_pt_br": course_pt_br,
            "course_en": course_en,
            "course_es": course_es,
            "course_id": course_id,
            "performance": performance,
            "performance_pt_br": performance_pt_br,
            "performance_en": performance_en,
            "performance_es": performance_es,
            "old_status": old_status,
            "status": status,
            "mandatory": mandatory,
        }
        return self._base_requests.put(path=path, json=data, parameters=parameters)

    def delete_training(
        self,
        _id: int,
        created__gt: datetime = None,
        created__lt: datetime = None,
        modified__gt: datetime = None,
        modified__lt: datetime = None,
        status: Literal[
            "pending",
            "pending_renovation",
            "in_progress",
            "concluded",
            "failed",
            "suspended",
            "canceled",
            "closed",
        ] = None,
    ) -> dict:
        """
        Delete training record
        Args:
            created__gt (datetime, Optional): Datetime to apply filter ">=" on created dates.
                Format "%Y-%m-%d %H:%M:%S"
            created__lt (datetime, Optional): Datetime to apply filter "<=" on created dates.
                Format "%Y-%m-%d %H:%M:%S"
            modified__gt (datetime, Optional): Datetime to apply filter ">=" on modified dates.
                Format "%Y-%m-%d %H:%M:%S"
            modified__lt (datetime, Optional): Datetime to apply filter "<=" on modified dates.
                Format "%Y-%m-%d %H:%M:%S"
            status (str, Optional): The training status
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
            "page_size": self.page_size,
            "status": status,
        }
        return self._base_requests.delete(path=path, parameters=parameters)

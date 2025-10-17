"""This module provide methods to work with areas entity"""

from datetime import date, datetime
from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from mindsight_full_api.settings import (
    API_ENDPOINT_PEOPLE,
    DATE_FORMAT,
    DATETIME_FORMAT,
)
from mindsight_full_api.utils.aux_functions import generate_url


class People(ApiEndpoint):
    """This class abstract the person endpoint methods
    """

    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_PEOPLE)

    def get_list_people(
        self,
        search: str = None,
        first_name: str = None,
        first_name__icontains: str = None,
        last_name: str = None,
        last_name__icontains: str = None,
        email: str = None,
        email__icontains: str = None,
        user__username: str = None,
        registration_code: str = None,
        gender: str = None,
        work_type: str = None,
        cpf: str = None,
        cpf__icontains: str = None,
        birth_date: str = None,
        birth_date__lt: str = None,
        birth_date__gt: str = None,
        alert__isnull: str = None,
        alert_search: str = None,
        salary_search: str = None,
        company_time_search: str = None,
        last_evaluation_search: str = None,
        last_position_search: str = None,
        last_manager_search: str = None,
        area_search: str = None,
        work_city: str = None,
        contract: str = None,
        only_top_hierarchy: str = None,
        active_alerts: str = None,
        training_status: str = None,
        ordering: str = None,
    ) -> ApiPaginationResponse:
        """
        get person records
        Args:
            }
        """

        path = ""
        parameters = {
            "search": search,
            "first_name": first_name,
            "first_name__icontains": first_name__icontains,
            "last_name": last_name,
            "last_name__icontains": last_name__icontains,
            "email": email,
            "email__icontains": email__icontains,
            "user__username": user__username,
            "registration_code": registration_code,
            "gender": gender,
            "work_type": work_type,
            "cpf": cpf,
            "cpf__icontains": cpf__icontains,
            "birth_date": birth_date,
            "birth_date__lt": birth_date__lt,
            "birth_date__gt": birth_date__gt,
            "alert__isnull": alert__isnull,
            "alert_search": alert_search,
            "salary_search": salary_search,
            "company_time_search": company_time_search,
            "last_evaluation_search": last_evaluation_search,
            "last_position_search": last_position_search,
            "last_manager_search": last_manager_search,
            "area_search": area_search,
            "work_city": work_city,
            "contract": contract,
            "only_top_hierarchy": only_top_hierarchy,
            "active_alerts": active_alerts,
            "training_status": training_status,
            "ordering": ordering,
            "page_size": self.page_size,
        }
        return ApiPaginationResponse(
            **self._base_requests.get(path=path, parameters=parameters).json(),
            headers=self._base_requests.headers,
        )

    def get_list_all_people(
        self,
    ) -> ApiPaginationResponse:
        """
        get person records
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
        path = "/get_all_employees"
        parameters = {
            "page_size": self.page_size,
        }
        return ApiPaginationResponse(
            **self._base_requests.get(path=path, parameters=parameters).json(),
            headers=self._base_requests.headers,
        )

    def post_create_person(
        self,
        first_name: str,
        last_name: str,
        uuid: str = None,
        registration_code: str = None,
        required: str = None,
        required_attr: str = None,
        email: str = None,
        gender: str = None,
        cpf: str = None,
        birth_date: str = None,
        company_referral: str = None,
        photo: str = None,
        work_type: str = None,
        work_city: str = None,
        user: int = None,
    ):
        """
        Create person record
        Args:
            date (date, Mandatory):
            amount (float, Mandatory):
            person_id (int, Mandatory):
            reference_date (date, Optional):
            reference_label(str, Optional):
            type (str, Optional):
        """
        path = ""
        data = {
            "first_name": first_name,
            "last_name": last_name,
            "uuid": uuid,
            "registration_code": registration_code,
            "required": required,
            "required_attr": required_attr,
            "email": email,
            "gender": gender,
            "cpf": cpf,
            "birth_date": birth_date,
            "company_referral": company_referral,
            "photo": photo,
            "work_type": work_type,
            "work_city": work_city,
            "user": user,
        }
        return self._base_requests.post(path=path, json=data)

    def get_person(
        self,
        _id: int,
        search: str = None,
        first_name: str = None,
        first_name__icontains: str = None,
        last_name: str = None,
        last_name__icontains: str = None,
        email: str = None,
        email__icontains: str = None,
        user__username: str = None,
        registration_code: str = None,
        gender: str = None,
        work_type: str = None,
        cpf: str = None,
        cpf__icontains: str = None,
        birth_date: str = None,
        birth_date__lt: str = None,
        birth_date__gt: str = None,
        alert__isnull: str = None,
        alert_search: str = None,
        salary_search: str = None,
        company_time_search: str = None,
        last_evaluation_search: str = None,
        last_position_search: str = None,
        last_manager_search: str = None,
        area_search: str = None,
        work_city: str = None,
        contract: str = None,
        only_top_hierarchy: str = None,
        active_alerts: str = None,
        training_status: str = None,
        ordering: str = None,
    ) -> dict:
        """
        Get person record
        Args:
            _id (int, Mandatory): Id of person record to retrieve
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
            "first_name": first_name,
            "first_name__icontains": first_name__icontains,
            "last_name": last_name,
            "last_name__icontains": last_name__icontains,
            "email": email,
            "email__icontains": email__icontains,
            "user__username": user__username,
            "registration_code": registration_code,
            "gender": gender,
            "work_type": work_type,
            "cpf": cpf,
            "cpf__icontains": cpf__icontains,
            "birth_date": birth_date,
            "birth_date__lt": birth_date__lt,
            "birth_date__gt": birth_date__gt,
            "alert__isnull": alert__isnull,
            "alert_search": alert_search,
            "salary_search": salary_search,
            "company_time_search": company_time_search,
            "last_evaluation_search": last_evaluation_search,
            "last_position_search": last_position_search,
            "last_manager_search": last_manager_search,
            "area_search": area_search,
            "work_city": work_city,
            "contract": contract,
            "only_top_hierarchy": only_top_hierarchy,
            "active_alerts": active_alerts,
            "training_status": training_status,
            "ordering": ordering,
        }
        return self._base_requests.get(
            path=path,
            parameters=parameters,
        )

    def put_edit_person(
        self,
        _id: int,
        uuid: str = None,
        registration_code: str = None,
        first_name: str = None,
        required: str = None,
        last_name: str = None,
        required_attr: str = None,
        email: str = None,
        gender: str = None,
        cpf: str = None,
        birth_date: str = None,
        company_referral: str = None,
        photo: str = None,
        work_type: str = None,
        work_city: str = None,
        user: str = None,
        search: str = None,
        first_name_param: str = None,
        first_name__icontains: str = None,
        last_name_param: str = None,
        last_name__icontains: str = None,
        email_param: str = None,
        email__icontains: str = None,
        user__username: str = None,
        registration_code_param: str = None,
        gender_param: str = None,
        work_type_param: str = None,
        cpf_param: str = None,
        cpf__icontains: str = None,
        birth_date_param: str = None,
        birth_date__lt: str = None,
        birth_date__gt: str = None,
        alert__isnull: str = None,
        alert_search: str = None,
        salary_search: str = None,
        company_time_search: str = None,
        last_evaluation_search: str = None,
        last_position_search: str = None,
        last_manager_search: str = None,
        area_search: str = None,
        work_city_param: str = None,
        contract: str = None,
        only_top_hierarchy: str = None,
        active_alerts: str = None,
        training_status: str = None,
        ordering: str = None,
    ) -> dict:
        """
        Update person record
        Args:
            _id (int, Mandatory): The person record id to update
        """
        path = f"/{_id}"
        data = {
            "uuid": uuid,
            "registration_code": registration_code,
            "first_name": first_name,
            "required": required,
            "last_name": last_name,
            "required_attr": required_attr,
            "email": email,
            "gender": gender,
            "cpf": cpf,
            "birth_date": birth_date,
            "company_referral": company_referral,
            "photo": photo,
            "work_type": work_type,
            "work_city": work_city,
            "user": user,
        }
        parameters = {
            "search": search,
            "first_name": first_name_param,
            "first_name__icontains": first_name__icontains,
            "last_name": last_name_param,
            "last_name__icontains": last_name__icontains,
            "email": email_param,
            "email__icontains": email__icontains,
            "user__username": user__username,
            "registration_code": registration_code_param,
            "gender": gender_param,
            "work_type": work_type_param,
            "cpf": cpf_param,
            "cpf__icontains": cpf__icontains,
            "birth_date": birth_date_param,
            "birth_date__lt": birth_date__lt,
            "birth_date__gt": birth_date__gt,
            "alert__isnull": alert__isnull,
            "alert_search": alert_search,
            "salary_search": salary_search,
            "company_time_search": company_time_search,
            "last_evaluation_search": last_evaluation_search,
            "last_position_search": last_position_search,
            "last_manager_search": last_manager_search,
            "area_search": area_search,
            "work_city": work_city_param,
            "contract": contract,
            "only_top_hierarchy": only_top_hierarchy,
            "active_alerts": active_alerts,
            "training_status": training_status,
            "ordering": ordering,
        }
        return self._base_requests.put(path=path, json=data, parameters=parameters)

    def delete_person(
        self,
        _id: int,
    ) -> dict:
        """
        Delete person record
        Args:
            _id (int, Mandatory): The person record id to delete
        """
        path = f"/{_id}"
        return self._base_requests.delete(
            path=path,
        )

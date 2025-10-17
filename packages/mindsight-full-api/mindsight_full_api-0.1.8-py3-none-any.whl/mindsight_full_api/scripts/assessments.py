"""This module provide methods to work with areas entity"""

from datetime import date, datetime
from mindsight_full_api.helpers.models import (
    ApiEndpoint,
    ApiPaginationResponse,
)
from mindsight_full_api.settings import (
    API_ENDPOINT_ASSESSMENTS,
    API_ENDPOINT_PEOPLE,
)
from mindsight_full_api.utils.aux_functions import generate_url


class Assessments(ApiEndpoint):
    """This class abstract the assessments endpoint methods
    """

    def __init__(self) -> None:
        super().__init__(API_ENDPOINT_ASSESSMENTS)

    def get_list_assessments(
        self,
    ) -> ApiPaginationResponse:
        """
        get assessments records
        Args:
            page (int, Optional):
        """

        path = ""
        parameters = {
            "page_size": self.page_size,
        }
        return ApiPaginationResponse(
            **self._base_requests.get(path=path, parameters=parameters).json(),
            headers=self._base_requests.headers,
        )

    def post_create_assessments(
        self,
        raw_potential: float = None,
        required: float = None,
        logic: float = None,
        social: float = None,
        motivational: float = None,
        cultural_fit: float = None,
        analytical_capacity: float = None,
        conceptual_thinking: float = None,
        reflection: float = None,
        creative_thinking: float = None,
        planning: float = None,
        communication: float = None,
        empathy: float = None,
        influence: float = None,
        sociability: float = None,
        facilitation: float = None,
        flexibility: float = None,
        emotional_stability: float = None,
        ambition: float = None,
        initiative: float = None,
        assertiveness: float = None,
        risk_taking: float = None,
        person_id: int = None,
    ):
        """
        Create assessments record
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
            "raw_potential": raw_potential,
            "required": required,
            "logic": logic,
            "social": social,
            "motivational": motivational,
            "cultural_fit": cultural_fit,
            "analytical_capacity": analytical_capacity,
            "conceptual_thinking": conceptual_thinking,
            "reflection": reflection,
            "creative_thinking": creative_thinking,
            "planning": planning,
            "communication": communication,
            "empathy": empathy,
            "influence": influence,
            "sociability": sociability,
            "facilitation": facilitation,
            "flexibility": flexibility,
            "emotional_stability": emotional_stability,
            "ambition": ambition,
            "initiative": initiative,
            "assertiveness": assertiveness,
            "risk_taking": risk_taking,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
        }

        return self._base_requests.post(path=path, json=data)

    def get_assessments(
        self,
        _id: int,
    ) -> dict:
        """
        Get assessments record
        Args:
            _id (int, Mandatory): Id of assessments record to retrieve
        """
        path = f"/{_id}"
        return self._base_requests.get(
            path=path,
        )

    def patch_edit_assessments(
        self,
        _id: int,
        person_id: int,
        raw_potential: float = None,
        required: float = None,
        logic: float = None,
        social: float = None,
        motivational: float = None,
        cultural_fit: float = None,
        analytical_capacity: float = None,
        conceptual_thinking: float = None,
        reflection: float = None,
        creative_thinking: float = None,
        planning: float = None,
        communication: float = None,
        empathy: float = None,
        influence: float = None,
        sociability: float = None,
        facilitation: float = None,
        flexibility: float = None,
        emotional_stability: float = None,
        ambition: float = None,
        initiative: float = None,
        assertiveness: float = None,
        risk_taking: float = None,
    ) -> dict:
        """
        Update assessments record
        Args:
            _id (int, Mandatory): The assessments record id to update
        """

        path = f"/{_id}"
        data = {
            "raw_potential": raw_potential,
            "required": required,
            "logic": logic,
            "social": social,
            "motivational": motivational,
            "cultural_fit": cultural_fit,
            "analytical_capacity": analytical_capacity,
            "conceptual_thinking": conceptual_thinking,
            "reflection": reflection,
            "creative_thinking": creative_thinking,
            "planning": planning,
            "communication": communication,
            "empathy": empathy,
            "influence": influence,
            "sociability": sociability,
            "facilitation": facilitation,
            "flexibility": flexibility,
            "emotional_stability": emotional_stability,
            "ambition": ambition,
            "initiative": initiative,
            "assertiveness": assertiveness,
            "risk_taking": risk_taking,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
        }

        return self._base_requests.patch(path=path, json=data)

    def put_edit_assessments(
        self,
        _id: int,
        person_id: int,
        raw_potential: float = None,
        required: float = None,
        logic: float = None,
        social: float = None,
        motivational: float = None,
        cultural_fit: float = None,
        analytical_capacity: float = None,
        conceptual_thinking: float = None,
        reflection: float = None,
        creative_thinking: float = None,
        planning: float = None,
        communication: float = None,
        empathy: float = None,
        influence: float = None,
        sociability: float = None,
        facilitation: float = None,
        flexibility: float = None,
        emotional_stability: float = None,
        ambition: float = None,
        initiative: float = None,
        assertiveness: float = None,
        risk_taking: float = None,
    ) -> dict:
        """
        Update assessments record
        Args:
            _id (int, Mandatory): The assessments record id to update
        """
        path = f"/{_id}"
        data = {
            "raw_potential": raw_potential,
            "required": required,
            "logic": logic,
            "social": social,
            "motivational": motivational,
            "cultural_fit": cultural_fit,
            "analytical_capacity": analytical_capacity,
            "conceptual_thinking": conceptual_thinking,
            "reflection": reflection,
            "creative_thinking": creative_thinking,
            "planning": planning,
            "communication": communication,
            "empathy": empathy,
            "influence": influence,
            "sociability": sociability,
            "facilitation": facilitation,
            "flexibility": flexibility,
            "emotional_stability": emotional_stability,
            "ambition": ambition,
            "initiative": initiative,
            "assertiveness": assertiveness,
            "risk_taking": risk_taking,
            "person": generate_url(base_path=API_ENDPOINT_PEOPLE, path=f"/{person_id}"),
        }
        return self._base_requests.put(path=path, json=data)

    def delete_assessments(
        self,
        _id: int,
    ) -> dict:
        """
        Delete assessments record
        Args:
            _id (int, Mandatory): The assessments record id to delete
        """
        path = f"/{_id}"
        return self._base_requests.delete(
            path=path,
        )

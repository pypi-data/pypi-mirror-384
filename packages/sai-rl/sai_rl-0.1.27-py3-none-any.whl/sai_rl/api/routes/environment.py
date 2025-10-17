from typing import Optional, List
from pydantic import ValidationError

from sai_rl.api.requestor import APIRequestor
from sai_rl.types import EnvironmentType
from sai_rl.error import InternalError


def parse_environment(environment: dict) -> EnvironmentType:
    try:
        return EnvironmentType.model_validate(environment)
    except ValidationError as e:
        raise InternalError(f"Error parsing environment: {e}", cause=e) from e


class EnvironmentAPI:
    def __init__(self, api: APIRequestor):
        self._api = api

    def get(self, environment_id: str) -> Optional[EnvironmentType]:
        response = self._api.get(f"/v1/environments/{environment_id}")

        raw_environment = response.json()
        if not raw_environment:
            return None

        return parse_environment(raw_environment)

    def list(self) -> Optional[List[EnvironmentType]]:
        response = self._api.get("/v1/environments")

        raw_environments = response.json()
        if not raw_environments:
            return None

        environments: List[EnvironmentType] = []

        for raw_environment in raw_environments:
            environments.append(parse_environment(raw_environment))

        return environments

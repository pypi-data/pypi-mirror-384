from typing import List, Optional
from pydantic import ValidationError

from sai_rl.types import CompetitionType
from sai_rl.api.requestor import APIRequestor
from sai_rl.error import InternalError


def parse_competition(competition: dict) -> CompetitionType:
    try:
        return CompetitionType.model_validate(competition)
    except ValidationError as e:
        raise InternalError(f"Error parsing competition: {e}", cause=e) from e


class CompetitionAPI:
    def __init__(self, api: APIRequestor):
        self._api = api

    def get(self, competition_id: str) -> Optional[CompetitionType]:
        response = self._api.get(f"/v1/competitions/{competition_id}")

        raw_competition = response.json()
        if not raw_competition:
            return None

        return parse_competition(raw_competition)

    def list(self) -> Optional[List[CompetitionType]]:
        response = self._api.get("/v1/competitions")

        raw_competitions = response.json()
        if not raw_competitions:
            return None

        competitions: List[CompetitionType] = []

        for raw_competition in raw_competitions:
            competitions.append(parse_competition(raw_competition))

        return competitions

from typing import Optional, List
from pydantic import ValidationError

from sai_rl.api.requestor import APIRequestor
from sai_rl.types import SubmissionType
from sai_rl.error import InternalError


def parse_submission(submission: dict) -> SubmissionType:
    try:
        return SubmissionType.model_validate(submission)
    except ValidationError as e:
        raise InternalError(f"Error parsing submission: {e}", cause=e) from e


class SubmissionAPI:
    def __init__(self, api: APIRequestor):
        self._api = api

    def list(self) -> Optional[List[SubmissionType]]:
        response = self._api.get("/v1/submissions")

        if not response:
            return None

        raw_submissions = response.json()
        if not raw_submissions:
            return None

        submissions: List[SubmissionType] = []

        for raw_submission in raw_submissions:
            submissions.append(parse_submission(raw_submission))

        return submissions

    def create(self, data: dict, files: dict) -> Optional[SubmissionType]:
        response = self._api.post("/v1/submissions", data=data, files=files)

        if not response:
            return None

        raw_submission = response.json()
        if not raw_submission:
            return None

        return parse_submission(raw_submission)

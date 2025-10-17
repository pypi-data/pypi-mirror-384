from typing import Optional, Union, Any, Literal
from pydantic import BaseModel

from sai_rl.types.environment import EnvironmentActionType, EnvironmentStandardType

ModelType = Any
ModelLibraryType = Literal[
    "pytorch", "tensorflow", "keras", "stable_baselines3", "onnx"
]


class SubmissionEnvironmentType(BaseModel):
    id: str
    name: str
    gymId: str
    type: EnvironmentStandardType
    actionType: EnvironmentActionType


class SubmissionCompetitionType(BaseModel):
    id: str
    slug: str
    name: str
    # environment: SubmissionEnvironmentType


class SubmissionType(BaseModel):
    id: str
    name: str
    type: str
    status: str
    score: Optional[Union[float, str]] = None
    competition: SubmissionCompetitionType
    updatedAt: str
    createdAt: str

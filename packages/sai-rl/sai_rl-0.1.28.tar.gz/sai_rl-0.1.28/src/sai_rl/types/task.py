from typing import Any, Mapping, Optional
from pydantic import BaseModel

from sai_rl.types.environment import EnvironmentType


class EvaluationFunctionType(BaseModel):
    version: int
    description: Optional[str] = None
    deleted: Optional[bool] = False
    createdAt: str


class TaskType(BaseModel):
    id: Optional[str] = None
    environment: EnvironmentType
    environmentVariables: Mapping[str, Any] = {}
    evaluationFnTimeline: Optional[list[EvaluationFunctionType]] = None
    evaluationFn: Optional[str] = None
    numberOfBenchmarks: Optional[int] = 1
    seed: Optional[int] = None
    scoreWeight: float = 1
    index: int = 0
    totalTaskCount: int = 1

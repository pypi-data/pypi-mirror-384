from typing import Literal, Union
from pydantic import BaseModel

from sai_rl.types.scene import SceneType
from sai_rl.types.environment import EnvironmentType
from sai_rl.types.task import TaskType


class LinkedBenchmarkType(BaseModel):
    collectionName: Literal["scenes", "environments"]
    document: Union[SceneType, EnvironmentType]


class CompetitionType(BaseModel):
    id: str
    slug: str
    name: str
    opensource: bool
    linkedBenchmark: LinkedBenchmarkType
    tasks: list[TaskType]

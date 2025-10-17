from pydantic import BaseModel

from sai_rl.types.environment import EnvironmentType


class SceneType(BaseModel):
    id: str
    name: str
    description: str
    environments: list[EnvironmentType]
    category: str
    tags: list[str]

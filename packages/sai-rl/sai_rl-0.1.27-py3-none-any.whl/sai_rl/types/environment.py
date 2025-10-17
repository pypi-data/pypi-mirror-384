from typing import Literal
from pydantic import BaseModel

from sai_rl.types.package import PackageType

EnvironmentActionType = Literal["discrete", "continuous"]
EnvironmentStandardType = Literal[
    "gymnasium", "gym-v26", "gym-v21", "pettingzoo", "pufferlib"
]


class EnvironmentType(BaseModel):
    id: str
    name: str
    gymId: str
    type: EnvironmentStandardType
    actionType: EnvironmentActionType
    package: PackageType

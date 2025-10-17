from typing import Optional, Literal
from pydantic import BaseModel


class EpisodeResults(BaseModel):
    score: float
    duration: float
    videoKey: Optional[str]


class BenchmarkTask(BaseModel):
    id: str
    status: Literal["success", "error", "failed"]
    score: Optional[float]
    duration: float
    episodes: list[EpisodeResults]


class BenchmarkResult(BaseModel):
    status: Literal["success", "error", "failed"]
    score: Optional[float]
    duration: float
    tasks: list[BenchmarkTask]
    logs: Optional[str]
    error: Optional[str]

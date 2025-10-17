from typing import Optional, List
from pydantic import ValidationError

from sai_rl.api.requestor import APIRequestor
from sai_rl.types import SceneType
from sai_rl.error import InternalError


def parse_scene(scene: dict) -> SceneType:
    try:
        return SceneType.model_validate(scene)
    except ValidationError as e:
        raise InternalError(f"Error parsing scene: {e}", cause=e) from e


class SceneAPI:
    def __init__(self, api: APIRequestor):
        self._api = api

    def get(self, scene_id: str) -> Optional[SceneType]:
        response = self._api.get(f"/v1/scenes/{scene_id}")

        raw_scene = response.json()
        if not raw_scene:
            return None

        return parse_scene(raw_scene)

    def list(self) -> Optional[List[SceneType]]:
        response = self._api.get("/v1/scenes")

        raw_scenes = response.json()
        if not raw_scenes:
            return None

        scenes: List[SceneType] = []

        for raw_scene in raw_scenes:
            scenes.append(parse_scene(raw_scene))

        return scenes

from abc import ABC, abstractmethod
from typing import Optional, Any

import numpy as np
import gymnasium as gym
import json
import hashlib

from sai_rl.sai_console import SAIConsole


class BaseModelHandler(ABC):
    """Base class for model handlers in SAI RL.
    This class provides an interface for loading, saving, and exporting models,
    as well as getting actions from the model.
    """

    _console: Optional[SAIConsole] = None

    is_continuous: bool
    obs_space_dims: int
    action_space: gym.Space
    observation_space: gym.Space
    sample_obs: np.ndarray
    sample_info: Any

    def __init__(
        self, env: Optional[gym.Env] = None, console: Optional[SAIConsole] = None
    ):
        self._console = console
        if env is not None:
            self._add_env(env)

    def _add_env(self, env: gym.Env):
        self.obs_space_dims = len(env.observation_space.sample().shape)
        self.is_continuous = isinstance(
            env.action_space, gym.spaces.Box
        ) and not np.issubdtype(env.action_space.dtype, np.integer)
        self.action_space = env.action_space
        self.observation_space = env.observation_space
        self.sample_obs, self.sample_info = env.reset()

    def _get_obs(self, preprocess_manager = None):
        obs = np.zeros(
            (1, *self.observation_space.shape),  # type: ignore
            dtype=self.observation_space.dtype,
        )
        if preprocess_manager is not None:
            obs = preprocess_manager.modify_state(obs, self.sample_info)
        return obs

    def set_obs_space_dims(self, dims):
        self.obs_space_dims = dims

    @abstractmethod
    def load_model(self, model_path: str):
        pass

    @abstractmethod
    def get_policy(self, model, obs: np.ndarray) -> np.ndarray:
        pass

    def get_action(self, model, obs: np.ndarray) -> np.ndarray:
        """Get action from the model given an observation.
        For discrete action spaces, returns argmax of policy distribution.
        For continuous action spaces, returns the policy values, which are assumed to be already scaled
        to the appropriate action range.
        """
        policy = self.get_policy(model, obs)
        if self.is_continuous:
            if np.all(np.isfinite(self.action_space.low)) and np.all(  # type: ignore
                np.isfinite(self.action_space.high)  # type: ignore
            ):
                expected_bounds = [-1, 1]
                action_percent = (policy - expected_bounds[0]) / (
                    expected_bounds[1] - expected_bounds[0]
                )
                bounded_percent = np.minimum(np.maximum(action_percent, 0), 1)
                return (
                    self.action_space.low  # type: ignore
                    + (self.action_space.high - self.action_space.low) * bounded_percent  # type: ignore
                )
            return policy

        if len(policy.shape) == 2:
            return np.argmax(policy, axis=1)

        return policy

    @abstractmethod
    def save_model(self, model, model_path: str, preprocess_manager = None):
        pass

    @abstractmethod
    def export_to_onnx(self, model, path: str):
        pass

    @abstractmethod
    def check_compliance(self, model):
        pass

    @abstractmethod
    def hash(self, model):
        return {}

    def _hash(self, model_json: str):
        serialized_str = json.dumps(model_json, sort_keys=True)
        return hashlib.sha256(serialized_str.encode("utf-8")).hexdigest()

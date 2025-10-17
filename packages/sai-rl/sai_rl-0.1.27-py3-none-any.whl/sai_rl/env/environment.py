from typing import Optional

import numpy as np
import gymnasium as gym

from sai_rl.env.custom_eval import ask_custom_eval_approval
from sai_rl.sai_console import SAIConsole
from sai_rl.types import TaskType
from sai_rl.utils import get_is_server

class TaskGymWrapper(gym.Wrapper):
    def __init__(self, env, task_index):
        super().__init__(env)
        self.task_index = task_index

    def reset(self, seed=None, options=None):
        obs, info = self.env.reset(seed=seed, options=options)
        info["task_index"] = self.task_index
        return obs, info        

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        info["task_index"] = self.task_index
        return obs, reward, terminated, truncated, info

def custom_eval_wrapper(
    task: TaskType,
    env: gym.Env,
    use_custom_eval: bool,
    competition_id: Optional[str] = None,
    console: Optional[SAIConsole] = None,
):
    is_server = get_is_server()
    evaluation_fn = task.evaluationFn
    task_index = np.eye(task.totalTaskCount, dtype=np.float32)[task.index]
    task_env = TaskGymWrapper(env, task_index)

    if evaluation_fn is None:
        return task_env

    if not is_server and competition_id is None:
        raise EnvironmentError(
            "Evaluation function found, but no competition loaded. Unexpected!"
        )

    if console and not use_custom_eval:
        console.info(
            "NOTE: This competition uses a custom evaluation, by setting 'use_custom_eval=False', the rewards will not match the server's evaluation."
        )
        return task_env

    if not is_server:
        has_approved_script = ask_custom_eval_approval(
            console, competition_id, evaluation_fn
        )
        if not has_approved_script:
            return task_env

    global_ns = {"np": np}
    exec(evaluation_fn, global_ns)
    evaluation_fn = global_ns.get("evaluation_fn")

    if not callable(evaluation_fn):
        return task_env

    class CustomEvaluationWrapper(gym.Wrapper):
        def __init__(self, env):
            super().__init__(env)
            self.evaluation_fn = evaluation_fn
            self.unwrapped_env = self.unwrap_env()
            self.eval_state = {}

        def unwrap_env(self):
            env = self.env
            while hasattr(env, "env"):
                env = env.env
            return env

        def reset(self, seed=None, options=None):
            obs, info = self.env.reset(seed=seed, options=options)
            info["task_index"] = task_index
            return obs, info

        def step(self, action):
            obs, reward, terminated, truncated, info = self.env.step(action)
            self.eval_state["terminated"] = terminated
            self.eval_state["truncated"] = truncated
            custom_reward, self.eval_state = self.evaluation_fn(
                self.unwrapped_env, self.eval_state
            )

            info["sai_custom_eval_reward"] = custom_reward
            info["sai_env_reward"] = reward
            info["task_index"] = task_index

            return obs, custom_reward, terminated, truncated, info

    env = CustomEvaluationWrapper(env)
    return env


def make_env_factory(
    task: TaskType,
    use_custom_eval: bool,
    competition_id: Optional[str] = None,
    console: Optional[SAIConsole] = None,
):
    env_id = task.environment.gymId
    env_type = task.environment.type
    task_vars = task.environmentVariables

    def env_factory(index=0, **kwargs):
        env_vars = {
            **(task_vars or {}),
            "index": index,
            "render_mode": "rgb_array",
            **kwargs,
        }
        if env_vars["render_mode"] is None:
            env_vars["render_mode"] = "rgb_array"

        env = None
        if env_type == "gymnasium":
            env = gym.make(env_id, **env_vars)
        elif env_type == "gym-v26":
            env = gym.make("GymV26Environment-v0", env_id=env_id, **env_vars)
        elif env_type == "gym-v21":
            env = gym.make("GymV21Environment-v0", env_id=env_id, **env_vars)
        elif env_type == "pufferlib":
            raise NotImplementedError(
                "Pufferlib is not supported in this version of 'sai_rl'."
            )
            # try:
            #     from pufferlib.emulation import GymnasiumPufferEnv
            #     from pufferlib.ocean import env_creator

            #     env = GymnasiumPufferEnv(
            #         env_creator=env_creator(env_id),
            #         env_kwargs=env_vars,
            #     )
            # except ImportError:
            #     raise ImportError(
            #         "Pufferlib is not installed. "
            #         "Please install it using \"pip install 'sai_rl[pufferlib]'\"."
            #     )
        else:
            raise EnvironmentError(
                f"Unsupported environment type: {env_type}. "
                "Please use a supported environment."
            )
        return custom_eval_wrapper(task, env, use_custom_eval, competition_id, console)

    return env_factory


def make_env(
    task: TaskType,
    use_custom_eval: bool = False,
    competition_id: Optional[str] = None,
    console: Optional[SAIConsole] = None,
    render_mode: Optional[str] = None,
    **kwargs,
):
    if competition_id and kwargs:
        console.warning(
            "Additional environment arguments will override competitions settings."
            "Your local environment may not match the competition configuration."
        )

    return make_env_factory(task, use_custom_eval, competition_id, console)(
        render_mode=render_mode, **kwargs
    )

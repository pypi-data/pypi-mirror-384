import numpy as np
import gymnasium as gym
from typing import Optional, Callable

from sai_rl.error import CustomCodeError
from sai_rl.sai_console import SAIConsole, SAIStatus
from sai_rl.model.custom.custom_code_manager import CustomCodeManager


class ActionFunctionManager(CustomCodeManager):
    def __init__(
        self,
        action_function: Optional[str | Callable] = None,
        env: Optional[gym.Env] = None,
        verbose: bool = False,
        console: Optional[SAIConsole] = None,
        status: Optional[SAIStatus] = None,
    ):
        super().__init__(
            action_function,
            "action",
            "function",
            env,
            verbose,
            console,
            status,
        )

    def get_action(self, policy: np.ndarray) -> np.ndarray:
        if self._code is None:
            raise CustomCodeError("Action function not loaded")

        return self._code(policy)  # type: ignore

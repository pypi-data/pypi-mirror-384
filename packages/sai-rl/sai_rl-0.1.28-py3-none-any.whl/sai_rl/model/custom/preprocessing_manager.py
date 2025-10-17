import numpy as np
import gymnasium as gym
from typing import Optional

from sai_rl.error import CustomCodeError
from sai_rl.sai_console import SAIConsole, SAIStatus
from sai_rl.model.custom.custom_code_manager import CustomCodeManager


class PreprocessingManager(CustomCodeManager):
    def __init__(
        self,
        preprocessor_class: Optional[str | type] = None,
        env: Optional[gym.Env] = None,
        verbose: bool = False,
        console: Optional[SAIConsole] = None,
        status: Optional[SAIStatus] = None,
    ):
        super().__init__(
            preprocessor_class,
            "preprocessing",
            "class",
            env,
            verbose,
            console,
            status,
        )

    def modify_state(self, state: np.ndarray, info={}) -> np.ndarray:
        if self._code is None:
            raise CustomCodeError("Preprocessor is not loaded")

        if not self.has_method("modify_state"):
            raise CustomCodeError(
                "Preprocessor class does not contain 'modify_state' method"
            )

        return self._code.modify_state(state, info)  # type: ignore

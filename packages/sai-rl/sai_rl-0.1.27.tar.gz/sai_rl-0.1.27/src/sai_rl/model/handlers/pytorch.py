from typing import Any, TYPE_CHECKING, Optional
from sai_rl.model.handlers._base import BaseModelHandler
from sai_rl.error import ModelError

from sai_rl.sai_console import SAIConsole

import json
import numpy as np
import gymnasium as gym

if TYPE_CHECKING:
    import torch
    import torch.nn as nn

    PyTorchModel = nn.Module
    PyTorchTensor = torch.Tensor
else:
    PyTorchModel = Any
    PyTorchTensor = Any

IMPORT_ERROR_MESSAGE = (
    "PyTorch is not installed. Please install it using 'pip install sai_rl[torch]'."
)


class PyTorchModelHandler(BaseModelHandler):
    _torch: Any = None
    _torch_available: bool = False

    _ignored_keys = {
        "_non_persistent_buffers_set",
        "_parameters",
        "_buffers",
        "_modules",
        "_backward_pre_hooks",
        "_backward_hooks",
        "_is_full_backward_hook",
        "_forward_hooks",
        "_forward_hooks_with_kwargs",
        "_forward_hooks_always_called",
        "_forward_pre_hooks",
        "_forward_pre_hooks_with_kwargs",
        "_state_dict_hooks",
        "_state_dict_pre_hooks",
        "_load_state_dict_pre_hooks",
        "_load_state_dict_post_hooks",
    }

    def __init__(
        self, env: Optional[gym.Env] = None, console: Optional[SAIConsole] = None
    ):
        super().__init__(env, console)
        try:
            import torch

            self._torch = torch
            self._torch_available = True
        except ImportError:
            self._torch_available = False
            raise ImportError(IMPORT_ERROR_MESSAGE)

    def _check_torch_available(self) -> None:
        if not self._torch_available:
            raise ImportError(IMPORT_ERROR_MESSAGE)

    def _safe_config(self, module):
        config = {}

        for k, v in vars(module).items():
            if k in {"_parameters", "_buffers", "_modules"}:
                continue
            if k in self._ignored_keys:
                continue

            if isinstance(
                v, (self._torch.nn.Parameter, self._torch.Tensor, self._torch.nn.Module)
            ):
                continue
            elif isinstance(v, float):
                config[k] = round(v, 8)
            elif isinstance(v, (int, str, bool, type(None), list, tuple, dict)):
                try:
                    json.dumps(v)
                    config[k] = v
                except TypeError:
                    config[k] = str(v)
            else:
                config[k] = str(type(v).__name__)

        return config

    def _serialize_architecture(self, model, params):
        def serialize_module(m: PyTorchModel):
            return {
                "class": type(m).__name__,
                "config": self._safe_config(m),
                "children": [serialize_module(child) for child in m.children()],
            }

        params_string = " <-> ".join([str(np.array(p).shape) for p in params])
        return {"architecture": serialize_module(model), "params_shape": params_string}

    def load_model(self, model_path: str) -> PyTorchModel:
        """
        Load a PyTorch model from the specified path.
        Args:
            model_path (str): Path to the model file.
        Returns:
            torch.nn.Module: The loaded PyTorch model.
        Raises:
            ImportError: If PyTorch is not installed.
        """
        self._check_torch_available()

        try:
            model = self._torch.jit.load(model_path)
            model.eval()
            return model
        except Exception as e:
            if self._console:
                self._console.error(
                    "Failed to load PyTorch model, you could try submitting with onnx by using sai.submit(..., use_onnx=True)"
                )
            raise ModelError(f"Failed to load PyTorch model: {e}")

    def get_policy(self, model: PyTorchModel, obs: np.ndarray) -> np.ndarray:
        """
        Get the action from the model given an observation.
        Args:
            model (torch.nn.Module): The PyTorch model.
            obs (np.ndarray): The observation input to the model.
            is_continuous (bool): If True, the model is for continuous action space.
        Returns:
            int: The action selected by the model.
        Raises:
            ImportError: If PyTorch is not installed.
        """
        self._check_torch_available()

        if len(obs.shape) < self.obs_space_dims + 1:
            obs = np.expand_dims(obs, axis=0)

        obs_tensor = self._torch.from_numpy(obs)
        model_pred = model(obs_tensor)
        if isinstance(model_pred, self._torch.Tensor):
            model_pred = model_pred.detach().numpy()
        return model_pred

    def save_model(self, model: PyTorchModel, model_path: str, preprocess_manager = None):
        """
        Save a PyTorch model to the specified path.
        Args:
            model (torch.nn.Module): The PyTorch model to save.
            model_path (str): Path to save the model file.
        Returns:
            str: The path to the saved model file.
        Raises:
            ImportError: If PyTorch is not installed.
        """
        self._check_torch_available()

        if not isinstance(model, self._torch.jit.ScriptModule):
            obs_tensor = self._torch.from_numpy(self._get_obs(preprocess_manager))

            model = self._torch.jit.trace(
                model,
                self._torch.randn(
                    *obs_tensor.shape,
                    dtype=obs_tensor.dtype,
                ),
            )
        self._torch.jit.save(model, model_path)

        return model_path

    def hash(self, model):
        params = [param.detach().cpu().tolist() for param in model.parameters()]
        return {
            "architecture": self._hash(
                json.dumps(self._serialize_architecture(model, params), sort_keys=True)
            ),
            "parameters": self._hash(json.dumps(params, sort_keys=True)),
        }

    def check_compliance(self, model):
        errors = []

        # Check 1: Inherits from torch.nn.Module
        if not isinstance(model, self._torch.nn.Module):
            errors.append("Model must inherit from torch.nn.Module")

        # Check 2: Has a `forward` method
        if not hasattr(model, "forward") or not callable(model.forward):
            errors.append(
                "Model must implement a callable `forward(self, inputs)` method"
            )

        # Check 3: Perform inference
        # TBD

        if errors:
            print("[PyTorch Compliance Errors]")
            for err in errors:
                print(f"- {err}")
            return False

        return True

    def export_to_onnx(self, model: PyTorchModel, model_path: str = None):
        self._check_torch_available()
        model.eval()

        torch_input = self._torch.from_numpy(
            np.zeros(
                (2, *self.observation_space.shape),  # type: ignore
                dtype=self.observation_space.dtype,
            )
        )

        onnx_model = self._torch.onnx.export(
            model,
            (torch_input,),
            export_params=True,
            opset_version=20,
            input_names=["input"],
            output_names=["output"],
            dynamo=True,
            dynamic_shapes=({0: self._torch.export.dynamic_shapes.Dim.DYNAMIC},),
            verbose=False,
        )

        if model_path:
            onnx_model.save(model_path)

        return onnx_model

from typing import Any, Optional, Dict
from sai_rl.model.handlers._base import BaseModelHandler
from sai_rl.error import ModelError

from sai_rl.sai_console import SAIConsole

import numpy as np
import gymnasium as gym
import json

try:
    import onnxruntime as ort
except ImportError:
    ort = None

IMPORT_ERROR_MESSAGE = (
    "ONNX Runtime is not installed. Please install it using 'pip install onnxruntime'."
)


class OnnxModelHandler(BaseModelHandler):
    _ort: Any = None
    _ort_available: bool = False

    def __init__(
        self, env: Optional[gym.Env] = None, console: Optional[SAIConsole] = None
    ):
        super().__init__(env, console)
        try:
            import onnxruntime as ort

            self._ort = ort
            self._ort_available = True
        except ImportError:
            self._ort_available = False
            raise ImportError(IMPORT_ERROR_MESSAGE)

    def _check_ort_available(self) -> None:
        if not self._ort_available:
            raise ImportError(IMPORT_ERROR_MESSAGE)

    def load_model(self, model_path: str):
        self._check_ort_available()
        try:
            return self._ort.InferenceSession(
                model_path,
                providers=["CPUExecutionProvider"],
            )
        except Exception as e:
            raise ModelError(f"Failed to load ONNX model: {e}")

    def get_policy(self, model: Any, obs: np.ndarray):
        """
        Get the action from the model given an observation.
        Args:
            model (onnxruntime.InferenceSession): The ONNX model.
            obs (np.ndarray): The observation input to the model.
            is_continuous (bool): If True, the model is for continuous action space.
        Returns:
            int: The action selected by the model.
        Raises:
            ImportError: If PyTorch is not installed.
        """

        self._check_ort_available()

        if len(obs.shape) < self.obs_space_dims + 1:
            obs = np.expand_dims(obs, axis=0)

        # Get the actual input name from the model
        input_name = model.get_inputs()[0].name

        # Create input dictionary with the correct input name
        input_dict = {input_name: obs}

        try:
            return model.run(None, input_dict)[0]
        except Exception as e:
            input_names = [inp.name for inp in model.get_inputs()]
            if self._console:
                self._console.error(
                    f"Failed to run ONNX model with input '{input_name}'. "
                    f"Available inputs: {input_names}"
                )
            raise ModelError(f"ONNX model execution failed: {e}")

    def save_model(self, model, model_path, preprocess_manager = None):
        self._check_ort_available()
        if self._console:
            self._console.warning(
                "Saving ONNX models is not supported. The model will not be saved."
            )
        pass

    def check_compliance(self, model):
        return True

    def export_to_onnx(self, model, model_path):
        self._check_ort_available()
        if self._console:
            self._console.warning(
                "Exporting to ONNX is not supported. The model will not be exported."
            )
        pass

    def _onnx_type_to_numpy_type(self, onnx_type):
        """Convert ONNX data type to numpy data type."""
        # ONNX type mapping to numpy types
        type_map = {
            1: np.float32,  # FLOAT
            2: np.uint8,  # UINT8
            3: np.int8,  # INT8
            4: np.uint16,  # UINT16
            5: np.int16,  # INT16
            6: np.int32,  # INT32
            7: np.int64,  # INT64
            8: str,  # STRING
            9: bool,  # BOOL
            10: np.float16,  # FLOAT16
            11: np.float64,  # DOUBLE
            12: np.uint32,  # UINT32
            13: np.uint64,  # UINT64
        }
        return type_map.get(onnx_type, np.float32)

    def _get_parameters_array(self, model):
        self._check_ort_available()
        if hasattr(model, "_model_path"):
            import onnx

            onnx_model = onnx.load(model._model_path)
            model_proto = onnx_model
        else:
            model_proto = None

        parameters = []

        if model_proto is not None:
            for initializer in model_proto.graph.initializer:
                if initializer.raw_data:
                    tensor_data = np.frombuffer(
                        initializer.raw_data,
                        dtype=self._onnx_type_to_numpy_type(initializer.data_type),
                    )

                    if initializer.dims:
                        tensor_data = tensor_data.reshape(initializer.dims)

                    parameters.append(tensor_data.tolist())
                else:
                    if hasattr(initializer, "float_data") and initializer.float_data:
                        parameters.append(list(initializer.float_data))
                    elif hasattr(initializer, "int64_data") and initializer.int64_data:
                        parameters.append(list(initializer.int64_data))
                    elif hasattr(initializer, "int32_data") and initializer.int32_data:
                        parameters.append(list(initializer.int32_data))
        return parameters

    def _infer_architecture(self, model) -> Dict[str, Any]:
        self._check_ort_available()

        inputs_meta = model.get_inputs()
        outputs_meta = model.get_outputs()

        architecture: Dict[str, Any] = {"inputs": [], "outputs": []}

        for input_info in inputs_meta:
            input_data = {
                "name": input_info.name,
                "shape": list(input_info.shape)
                if hasattr(input_info, "shape")
                else None,
                "type": str(input_info.type) if hasattr(input_info, "type") else None,
            }
            architecture["inputs"].append(input_data)

        for output_info in outputs_meta:
            output_data = {
                "name": output_info.name,
                "shape": list(output_info.shape)
                if hasattr(output_info, "shape")
                else None,
                "type": str(output_info.type) if hasattr(output_info, "type") else None,
            }
            architecture["outputs"].append(output_data)

        # Add action and observation space info
        architecture["spaces"] = {
            "observation_space": {
                "shape": list(self.observation_space.shape)
                if self.observation_space.shape
                else None,
                "dtype": str(self.observation_space.dtype),
            },
            "action_space": {
                "shape": list(self.action_space.shape)
                if hasattr(self.action_space, "shape") and self.action_space.shape
                else None,
                "dtype": str(self.action_space.dtype)
                if hasattr(self.action_space, "dtype")
                else None,
                "is_continuous": self.is_continuous,
            },
        }

        return architecture

    def hash(self, model):
        self._check_ort_available()

        return {
            "architecture": self._hash(
                json.dumps(self._infer_architecture(model), sort_keys=True)
            ),
            "parameters": self._hash(
                json.dumps(self._get_parameters_array(model), sort_keys=True)
            ),
        }

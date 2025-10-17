import json
from typing import Optional, Any

from sai_rl.model.handlers._base import BaseModelHandler
from sai_rl.error import ModelError
from sai_rl.sai_console import SAIConsole

import gymnasium as gym
import numpy as np

IMPORT_ERROR_MESSAGE = (
    "TensorFlow is not installed. Please install it using 'pip install sai_rl[tf]'."
)


class KerasModelHandler(BaseModelHandler):
    _tf: Any = None
    _keras: Any = None
    _tf2onnx: Any = None
    _onnx: Any = None
    _tf_available: bool = False

    def __init__(
        self, env: Optional[gym.Env] = None, console: Optional[SAIConsole] = None
    ):
        super().__init__(env, console)
        try:
            import tensorflow as tf
            import keras
            import tf2onnx
            import onnx

            self._tf = tf
            self._keras = keras
            self._tf2onnx = tf2onnx
            self._onnx = onnx
            self._tf_available = True
            pass
        except ImportError:
            self._tf_available = False
            raise ImportError(IMPORT_ERROR_MESSAGE)

    def _check_tensorflow_available(self) -> None:
        if not self._tf_available:
            raise ImportError(IMPORT_ERROR_MESSAGE)

    def load_model(self, model_path):
        self._check_tensorflow_available()
        try:
            return self._keras.models.load_model(model_path)
        except Exception as e:
            raise ModelError(f"Failed to load Keras model: {e}")

    def get_policy(self, model, obs: np.ndarray) -> np.ndarray:
        self._check_tensorflow_available()

        if len(obs.shape) < self.obs_space_dims + 1:
            obs = np.expand_dims(obs, axis=0)

        # state = self._tf.convert_to_tensor(obs, dtype=self.observation_space.dtype)
        state = self._tf.convert_to_tensor(obs)
        policy = model(state)
        return np.array(policy)

    def save_model(self, model, model_path, preprocess_manager = None):
        self._check_tensorflow_available()
        inference_model = self.convert_to_sequential(model, preprocess_manager)
        inference_model.save(model_path)

    def convert_to_sequential(self, model, preprocess_manager = None):
        if type(model).__name__ == "Sequential":
            return model
        obs = self._get_obs(preprocess_manager)
        hidden_layers = model.get_hidden_layers()
        output_layer = model.get_output_layer()
        inference_model = self._keras.Sequential(
            [
                self._keras.layers.InputLayer(shape=obs.shape),
                *hidden_layers,
                output_layer,
            ]
        )

        for src_layer, dst_layer in zip(
            [*hidden_layers, output_layer], inference_model.layers
        ):
            dst_layer.set_weights(src_layer.get_weights())

        return inference_model

    def hash(self, model):
        formatted_model = self.convert_to_sequential(model)
        return {
            "architecture": self._hash(formatted_model.to_json()),
            "parameters": self._hash(
                json.dumps(
                    [w.tolist() for w in formatted_model.get_weights()], sort_keys=True
                )
            ),
        }

    def check_compliance(self, model):
        errors = []

        # Check 1: Inherits from keras.Model
        if not isinstance(model, self._keras.Model):
            errors.append("Model must inherit from keras.Model")

        # Check 2: Has a `call` method
        if not hasattr(model, "call") or not callable(model.call):
            errors.append("Model must implement a callable `call(self, inputs)` method")

        # Check 3: Perform inference
        # TBD

        if errors:
            print("[Keras Compliance Errors]")
            for err in errors:
                print(f"- {err}")
            return False

        return True

    def export_to_onnx(self, model, model_path: str):
        self._check_tensorflow_available()

        model.output_names = ["output"]
        input_signature = [
            self._tf.TensorSpec(
                [None, *self.observation_space.sample().shape],
                self._tf.float32,
                name="input",
            )
        ]
        onnx_model, _ = self._tf2onnx.convert.from_keras(
            model, input_signature=input_signature, opset=18
        )
        self._onnx.save(
            onnx_model,
            model_path if model_path.endswith(".onnx") else f"{model_path}.onnx",
        )

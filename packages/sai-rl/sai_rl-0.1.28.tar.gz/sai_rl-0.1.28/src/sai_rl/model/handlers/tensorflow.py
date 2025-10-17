from typing import Optional, Any

from sai_rl.model.handlers._base import BaseModelHandler
from sai_rl.error import ModelError
from sai_rl.sai_console import SAIConsole

import gymnasium as gym
import numpy as np
import tarfile
import tempfile
import json

IMPORT_ERROR_MESSAGE = (
    "TensorFlow is not installed. Please install it using 'pip install sai_rl[tf]'."
)


class TensorFlowModelHandler(BaseModelHandler):
    _tf: Any = None
    _tf_v1: Any = None
    _tf2onnx: Any = None
    _onnx: Any = None
    _tf_available: bool = False

    def __init__(
        self, env: Optional[gym.Env] = None, console: Optional[SAIConsole] = None
    ):
        super().__init__(env, console)
        try:
            import tensorflow.compat.v1 as tf_v1
            import tensorflow as tf
            import tf2onnx
            import onnx

            self._tf = tf
            self._tf_v1 = tf_v1
            self._tf2onnx = tf2onnx
            self._onnx = onnx
            self._tf_available = True
        except ImportError:
            self._tf_available = False
            raise ImportError(IMPORT_ERROR_MESSAGE)

    def _check_tensorflow_available(self) -> None:
        if not self._tf_available:
            raise ImportError(IMPORT_ERROR_MESSAGE)

    def is_tf1_model(self, model) -> bool:
        return hasattr(model, "sess")

    def is_tf2_model(self, model) -> bool:
        return (callable(model) and hasattr(model, "__call__")) or isinstance(
            model, self._tf.Module
        )

    def load_model(self, model_path: str):
        self._check_tensorflow_available()

        model = None
        tf2_load_successful = False
        try:
            model = self._load_model_v2(model_path)
            tf2_load_successful = self.is_tf2_model(model)
        except Exception as e:
            print(f"TF2 model load failed: {str(e)}")

        if tf2_load_successful:
            return model
        elif model is not None:
            raise ValueError("Loaded TF2 model is not recognized as valid.")

        print("Falling back to TF1 model loader...")
        try:
            return self._load_model_v1(model_path)
        except Exception as e:
            raise ModelError(f"Failed to load TensorFlow model: {e}")

    def _load_model_v2(self, model_path):
        self._check_tensorflow_available()

        class TF2ModelWrapper:
            def __init__(self, model_path, tf):
                self.tf = tf
                temp_dir = tempfile.mkdtemp()
                with tarfile.open(model_path, "r") as tar:
                    tar.extractall(temp_dir)

                model = tf.saved_model.load(temp_dir)
                self.infer = model.signatures["serving_default"]
                self.output_key = list(self.infer.structured_outputs.keys())[0]

            def __call__(self, x):
                if x.ndim == 1:
                    x = np.expand_dims(x, axis=0)
                state = self.tf.convert_to_tensor(x, dtype=self.tf.float32)
                return self.infer(state)[self.output_key].numpy()

        return TF2ModelWrapper(model_path, self._tf)

    def _load_model_v1(self, model_path):
        self._check_tensorflow_available()

        self._tf_v1.disable_eager_execution()

        class FrozenTF1Model:
            def __init__(
                self,
                model_path: str,
                input_name: str = "states:0",
                output_name: str = "policy:0",
                tf=None,
            ):
                self.graph = tf.Graph()
                with tf.gfile.GFile(model_path, "rb") as f:
                    graph_def = tf.GraphDef()
                    graph_def.ParseFromString(f.read())

                with self.graph.as_default():
                    tf.import_graph_def(graph_def, name="")

                self.sess = tf.Session(graph=self.graph)
                self.states = self.graph.get_tensor_by_name(input_name)
                self.policy = self.graph.get_tensor_by_name(output_name)

            def select_action(self, state: np.ndarray):
                state = np.expand_dims(state, axis=0) if state.ndim == 1 else state
                return self.sess.run(self.policy, feed_dict={self.states: state})[0]

        return FrozenTF1Model(
            model_path, input_name="states:0", output_name="policy:0", tf=self._tf_v1
        )

    def _get_parameters_array(self, model):
        if self.is_tf1_model(model):
            values = model.sess.run(self._tf_v1.trainable_variables())
            return [v.tolist() for v in values]
        elif self.is_tf2_model(model):
            return [var.numpy().tolist() for var in model.variables]

    def _infer_architecture(self, model):
        if self.is_tf1_model(model):
            return self._infer_architecture_v1(model)
        elif self.is_tf2_model(model):
            return self._infer_architecture_v2(model)

    def _infer_architecture_v2(self, model):
        structure = []
        for var in model.variables:
            var_info = {
                "name": var.name,
                "shape": tuple(var.shape.as_list()),
                "dtype": str(var.dtype),
                "trainable": var.trainable,
            }
            structure.append(var_info)
        return structure

    def _infer_architecture_v1(self, model):
        graph = model.sess.graph
        graph_def = graph.as_graph_def()

        layers = []
        for node in graph_def.node:
            if node.op in {
                "MatMul",
                "Conv2D",
                "BiasAdd",
                "Relu",
                "Tanh",
                "Sigmoid",
                "Elu",
                "Softmax",
            }:
                layers.append(
                    {
                        "name": node.name,
                        "op": node.op,
                        "inputs": node.input[:],  # list of input tensor names
                    }
                )

        variables = []
        for var in self._tf_v1.trainable_variables():
            variables.append(
                {
                    "name": var.name,
                    "shape": tuple(var.shape.as_list()),
                    "dtype": var.dtype.name,
                }
            )

        return {
            "class": model.__class__.__name__,
            "layers": layers,
            "variables": variables,
        }

    def get_policy(self, model, obs: np.ndarray) -> np.ndarray:
        self._check_tensorflow_available()

        if len(obs.shape) < self.obs_space_dims + 1:
            obs = np.expand_dims(obs, axis=0)

        if self.is_tf1_model(model):
            return model.sess.run(model.policy, feed_dict={model.states: obs})
        elif self.is_tf2_model(model):
            return np.array(model(obs))
        elif hasattr(model, "predict"):
            return np.array(model.predict(obs, verbose=0))
        else:
            raise ValueError("Unknown model type: cannot compute policy.")

    @staticmethod
    def _save_as_pbx(source_dir, pbx_path):
        with tarfile.open(pbx_path, "w") as tar:
            tar.add(source_dir, arcname="")

    def save_model(self, model, model_path, preprocess_manager = None):
        self._check_tensorflow_available()

        if self.is_tf1_model(model):
            from tensorflow.compat.v1.graph_util import convert_variables_to_constants

            sess = model.sess
            output_node_names = [model.policy.name.split(":")[0]]
            frozen_graph_def = convert_variables_to_constants(
                sess, sess.graph.as_graph_def(), output_node_names=output_node_names
            )
            self._tf_v1.io.write_graph(
                frozen_graph_def, logdir=".", name=model_path, as_text=False
            )
        elif self.is_tf2_model(model):
            folder_name = model_path.replace(".pb", "")
            concrete_fn = model.get_concrete_function()
            self._tf.saved_model.save(
                model, folder_name, signatures={"serving_default": concrete_fn}
            )
            self._save_as_pbx(folder_name, folder_name + ".pbx")

        return model_path

    def _check_compliance_v1(self, model):
        errors = []

        # Check 1: Check `states` exists, is a placeholder, and named 'states'
        if not hasattr(model, "states"):
            errors.append("Model must have a `states` attribute")
        else:
            states = model.states
            if not isinstance(
                states, self._tf_v1.Tensor
            ) or not states.op.type.startswith("Placeholder"):
                errors.append("`states` must be a tf.placeholder")
            elif states.name.split(":")[0] != "states":
                errors.append("`states` placeholder must be named 'states'")

        # Check 2: Check `policy` exists
        if not hasattr(model, "policy"):
            errors.append("Model must have a `policy` attribute")
        else:
            policy = model.policy
            if not isinstance(policy, self._tf_v1.Tensor):
                errors.append("`policy` must be a tf.Tensor")
            elif policy.name.split(":")[0] != "policy":
                errors.append("`policy` tensor must be named 'policy'")

        # Check 3: Check `sess` exists and is a tf.Session
        if not hasattr(model, "sess"):
            errors.append("Model must have a `sess` attribute")
        elif not isinstance(model.sess, self._tf_v1.Session):
            errors.append("`sess` must be an instance of tf.Session")

        if errors:
            print("[TF1 Compliance Errors]")
            for err in errors:
                print(f"- {err}")
            return False

        return True

    def _check_compliance_v2(self, model):
        errors = []

        # Check 1: Inherits from tf.Module
        if not isinstance(model, self._tf.Module):
            errors.append("Model must inherit from tf.Module")

        # Check 2: Has a __call__ method
        if not hasattr(model, "__call__") or not callable(model.__call__):
            errors.append("Model must implement a callable `__call__(self, x)` method")

        # Optional: Check if __call__ is decorated with tf.function
        if hasattr(model.__call__, "get_concrete_function"):
            pass  # Good — it's decorated with @tf.function
        else:
            errors.append("`__call__` must be decorated with @tf.function")

        # Check 3: Has a get_concrete_function method that returns a ConcreteFunction
        if not hasattr(model, "get_concrete_function"):
            errors.append("Model must have a `get_concrete_function()` method")
        else:
            try:
                # Try to call it — requires model.n_features to be defined
                fn = model.get_concrete_function()
                if not isinstance(fn, self._tf.types.experimental.ConcreteFunction):
                    errors.append(
                        "`get_concrete_function()` must return a tf.ConcreteFunction"
                    )
            except Exception as e:
                errors.append(f"Calling `get_concrete_function()` failed: {str(e)}")

        if errors:
            print("[TF2 Compliance Errors]")
            for err in errors:
                print(f"- {err}")
            return False

        return True

    def check_compliance(self, model):
        if self.is_tf1_model(model):
            return self._check_compliance_v1(model)
        else:
            return self._check_compliance_v2(model)

    def export_to_onnx_v1(self, model, model_path: str):
        from tensorflow.compat.v1.graph_util import convert_variables_to_constants

        sess = model.sess
        input_names = [model.states.name]
        output_names = [model.policy.name]

        # Freeze variables into constants
        frozen_graph_def = convert_variables_to_constants(
            sess,
            sess.graph_def,
            output_node_names=[name.split(":")[0] for name in output_names],
        )

        onnx_model, _ = self._tf2onnx.convert.from_graph_def(
            frozen_graph_def,
            input_names=input_names,
            output_names=output_names,
            opset=11,
        )

        self._onnx.save_model(
            onnx_model,
            model_path if model_path.endswith(".onnx") else f"{model_path}.onnx",
        )

    def export_to_onnx_v2(self, model, model_path: str):
        input_shape = [None, *self.observation_space.shape]
        input_spec = self._tf.TensorSpec(input_shape, self._tf.float32, name="input")

        # Wrap model in a tracing function
        @self._tf.function
        def wrapped_model(x):
            return model(x)

        # Manually create concrete function
        concrete_func = wrapped_model.get_concrete_function(input_spec)

        onnx_model, _ = self._tf2onnx.convert.from_function(
            wrapped_model, input_signature=[input_spec], opset=11
        )

        self._onnx.save_model(
            onnx_model,
            model_path if model_path.endswith(".onnx") else f"{model_path}.onnx",
        )

    def hash(self, model):
        return {
            "architecture": self._hash(
                json.dumps(self._infer_architecture(model), sort_keys=True)
            ),
            "parameters": self._hash(
                json.dumps(self._get_parameters_array(model), sort_keys=True)
            ),
        }

    def export_to_onnx(self, model, model_path: str):
        self._check_tensorflow_available()
        if self.is_tf1_model(model):
            self.export_to_onnx_v1(model, model_path)
        elif self.is_tf2_model(model):
            self.export_to_onnx_v2(model, model_path)

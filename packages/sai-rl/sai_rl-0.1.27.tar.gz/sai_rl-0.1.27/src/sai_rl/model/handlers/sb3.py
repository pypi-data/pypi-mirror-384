import json
from typing import Any, TYPE_CHECKING, Optional
from sai_rl.model.handlers._base import BaseModelHandler
from sai_rl.error import ModelError

from sai_rl.sai_console import SAIConsole

import gymnasium as gym
import numpy as np

if TYPE_CHECKING:
    from stable_baselines3.common.policies import BasePolicy

    SB3BasePolicy = BasePolicy
else:
    SB3BasePolicy = Any

IMPORT_ERROR_MESSAGE = (
    "Stable Baselines3 is not installed. Please install it using 'pip install stable-baselines3'."
    " If you are using a custom model, please ensure it is compatible with Stable Baselines3."
)

SB3_ALGORITHMS = ["A2C", "DDPG", "DQN", "HER", "PPO", "SAC", "TD3"]


class SBL3ModelHandler(BaseModelHandler):
    _torch: Any = None
    _sb3: Any = None
    _sb3_available: bool = False

    def __init__(
        self,
        env: Optional[gym.Env] = None,
        console: Optional[SAIConsole] = None,
        algo="PPO",
    ):
        super().__init__(env, console)

        try:
            import stable_baselines3 as sb3
            import torch

            self._sb3 = sb3
            self._torch = torch
            self._sb3_available = True
        except ImportError:
            self._sb3_available = False
            raise ImportError(IMPORT_ERROR_MESSAGE)

        algo = algo.upper()
        if algo not in SB3_ALGORITHMS:
            raise ValueError(
                f"Algorithm {algo} is not supported. Please use one of the following: {SB3_ALGORITHMS}"
            )

        self._algo = getattr(sb3, algo)

        class SB3TorchPolicy(torch.nn.Module):
            def __init__(self, policy: SB3BasePolicy):
                super().__init__()
                self.policy = policy

            def forward(self, observation: torch.Tensor):
                return self.policy(observation, deterministic=True)

        self._policy_class = SB3TorchPolicy

    def _check_sb3_available(self) -> None:
        if not self._sb3_available:
            raise ImportError(
                "Stable Baselines3 is not installed. Please install it using 'pip install stable-baselines3'."
            )

    def load_model(self, model_path) -> SB3BasePolicy:
        try:
            return self._algo.load(model_path)
        except Exception as e:
            raise ModelError(
                f"Error loading SB3 model: {e}. The wrong model type may have been provided, default is PPO."
            ) from e

    def get_discrete_output(self, model, obs):
        if isinstance(obs, np.ndarray):
            obs_tensor = self._torch.as_tensor(obs).float().to(model.device)
        else:
            obs_tensor = obs.to(model.device)

        if len(obs_tensor.shape) == len(model.observation_space.shape):
            obs_tensor = obs_tensor.unsqueeze(0)

        with self._torch.no_grad():
            dist = model.policy.get_distribution(obs_tensor)

            if hasattr(dist, "distribution"):  # Categorical or DiagGaussian
                dist = dist.distribution

            if hasattr(dist, "probs"):  # Discrete: Categorical
                return dist.probs.cpu().numpy()
            elif hasattr(dist, "mean"):  # Continuous: DiagGaussian
                mean = dist.mean.cpu().numpy()
                std = dist.stddev.cpu().numpy()
                return {"mean": mean, "std": std}

    def get_policy(self, model: SB3BasePolicy, obs: Any) -> Any:
        policy = None
        if len(obs.shape) < self.obs_space_dims + 1:
            obs = np.expand_dims(obs, axis=0)

        is_continuous = getattr(
            self, "is_continuous", type(model.action_space).__name__ == "Box"
        )

        if not is_continuous:
            policy = self.get_discrete_output(model, obs)

        if policy is None:
            policy = model.predict(obs, deterministic=True)[0]

        return policy

    def get_action(self, model, obs: np.ndarray) -> np.ndarray:
        policy = self.get_policy(model, obs)
        if not self.is_continuous and len(policy.shape) == 2:
            return np.argmax(policy, axis=1)
        return policy

    def save_model(self, model, model_path, preprocess_manager = None):
        self._check_sb3_available()

        model.save(model_path)
        return model_path

    def check_compliance(self, model):
        return True

    def export_to_onnx(self, model: SB3BasePolicy, model_path: str):
        self._check_sb3_available()

        torch_model = self._policy_class(model.policy)  # type: ignore
        torch_model.eval()

        # Convert numpy dtype to torch dtype
        numpy_to_torch_dtype = {
            "float32": self._torch.float32,
            "float64": self._torch.float64,
            "int32": self._torch.int32,
            "int64": self._torch.int64,
        }

        obs_dtype_str = str(self.observation_space.dtype)
        torch_dtype = numpy_to_torch_dtype.get(obs_dtype_str, self._torch.float32)

        torch_input = self._torch.randn(
            1,
            *self.observation_space.shape,
            dtype=torch_dtype,
        )

        return self._torch.onnx.export(
            torch_model,
            (torch_input,),
            model_path,
            export_params=True,
            opset_version=18,
            input_names=["input"],
            output_names=["output"],
            dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
        )

    def _get_parameters_array(self, model: SB3BasePolicy):
        self._check_sb3_available()

        policy_params = []

        if hasattr(model, "policy") and hasattr(model.policy, "parameters"):
            for param in model.policy.parameters():
                policy_params.append(param.detach().cpu().numpy().tolist())

        if hasattr(model, "value_net") and hasattr(model.value_net, "parameters"):
            for param in model.value_net.parameters():
                policy_params.append(param.detach().cpu().numpy().tolist())

        if hasattr(model, "get_parameters"):
            params_dict = model.get_parameters()
            if "policy" in params_dict:
                policy_state = params_dict["policy"]
                for key, value in policy_state.items():
                    if hasattr(value, "detach"):
                        policy_params.append(value.detach().cpu().numpy().tolist())
                    elif isinstance(value, np.ndarray):
                        policy_params.append(value.tolist())

        return policy_params

    def _infer_architecture(self, model: SB3BasePolicy):
        self._check_sb3_available()

        architecture = {
            "class": model.__class__.__name__,
            "algorithm": getattr(model, "_get_name", lambda: "Unknown")(),
            "policy_class": model.policy.__class__.__name__
            if hasattr(model, "policy")
            else None,
            "layers": [],
            "network_architecture": {},
        }

        if hasattr(model, "policy"):
            policy = model.policy

            if hasattr(policy, "mlp_extractor"):
                # For on-policy algorithms like PPO, A2C
                mlp_extractor = policy.mlp_extractor
                if hasattr(mlp_extractor, "policy_net"):
                    for i, layer in enumerate(mlp_extractor.policy_net):
                        if hasattr(layer, "weight"):
                            architecture["layers"].append(
                                {
                                    "name": f"policy_layer_{i}",
                                    "type": layer.__class__.__name__,
                                    "input_features": layer.in_features
                                    if hasattr(layer, "in_features")
                                    else None,
                                    "output_features": layer.out_features
                                    if hasattr(layer, "out_features")
                                    else None,
                                    "activation": getattr(
                                        layer, "activation", None
                                    ).__class__.__name__
                                    if hasattr(layer, "activation")
                                    else None,
                                }
                            )

                if hasattr(mlp_extractor, "value_net"):
                    for i, layer in enumerate(mlp_extractor.value_net):
                        if hasattr(layer, "weight"):
                            architecture["layers"].append(
                                {
                                    "name": f"value_layer_{i}",
                                    "type": layer.__class__.__name__,
                                    "input_features": layer.in_features
                                    if hasattr(layer, "in_features")
                                    else None,
                                    "output_features": layer.out_features
                                    if hasattr(layer, "out_features")
                                    else None,
                                    "activation": getattr(
                                        layer, "activation", None
                                    ).__class__.__name__
                                    if hasattr(layer, "activation")
                                    else None,
                                }
                            )

            elif hasattr(policy, "q_net"):
                # For off-policy algorithms like DQN, SAC
                q_net = policy.q_net
                for i, layer in enumerate(q_net):
                    if hasattr(layer, "weight"):
                        architecture["layers"].append(
                            {
                                "name": f"q_layer_{i}",
                                "type": layer.__class__.__name__,
                                "input_features": layer.in_features
                                if hasattr(layer, "in_features")
                                else None,
                                "output_features": layer.out_features
                                if hasattr(layer, "out_features")
                                else None,
                            }
                        )

            if hasattr(policy, "net_arch"):
                architecture["network_architecture"]["net_arch"] = policy.net_arch

        if hasattr(model, "learning_rate"):
            architecture["hyperparameters"] = {
                "learning_rate": float(model.learning_rate)
                if callable(model.learning_rate)
                else model.learning_rate,
            }

        architecture["spaces"] = {
            "observation_space": {
                "shape": self.observation_space.shape,
                "dtype": str(self.observation_space.dtype),
            },
            "action_space": {
                "shape": self.action_space.shape
                if hasattr(self.action_space, "shape")
                else None,
                "dtype": str(self.action_space.dtype)
                if hasattr(self.action_space, "dtype")
                else None,
                "is_continuous": self.is_continuous,
            },
        }

        return architecture

    def hash(self, model: SB3BasePolicy):
        self._check_sb3_available()

        return {
            "architecture": self._hash(
                json.dumps(self._infer_architecture(model), sort_keys=True)
            ),
            "parameters": self._hash(
                json.dumps(self._get_parameters_array(model), sort_keys=True)
            ),
        }

from typing import Literal, Optional, Callable, Union
from io import StringIO
import json
import time

import os
import random
import string
import sys
import shutil
from pathlib import Path

from rich.table import Table
from rich.align import Align
from rich.text import Text

from sai_rl.benchmark.record import EpisodeType
from sai_rl.types import TaskType, EnvironmentType, CompetitionType, SceneType

from sai_rl.benchmark.types import BenchmarkResult, BenchmarkTask
from sai_rl.package import PackageControl
from sai_rl.env import make_env, make_env_factory
from sai_rl.sai_console import SAIConsole, SAIStatus
from sai_rl.utils import config, get_is_server, TeeIO
from sai_rl.error import (
    BenchmarkError,
    SceneError,
    CompetitionError,
    CustomCodeError,
    SubmissionError,
    SetupError,
    EnvironmentError,
    AuthenticationError,
    InternalError,
    ModelError,
)

from sai_rl.api import APIClient
from sai_rl.model import ModelManager
from sai_rl.types import ModelType, ModelLibraryType
from sai_rl.benchmark import (
    run_benchmark,
    record_episodes,
)


class SAIClient(object):
    """
    Main client for interacting with the SAI platform.

    The SAIClient provides methods for:
    - Loading competitions and environments from the SAI platform
    - Watching and benchmarking models
    - Creating and submitting models

    Args:
        env_id (Optional[str]): ID of environment to load
        api_key (Optional[str]): API key for authentication
        comp_id (Optional[str]): ID of competition to load
        api_base (Optional[str]): Custom API endpoint

    Examples:
        Basic usage:
        >>> sai = SAIClient("SquidHunt-v0")
        >>> sai.watch()  # Watch random agent

        Using a model:
        >>> model = torch.load("my_model.pt")
        >>> sai.benchmark(model)
    """

    def __init__(
        self,
        env_id: Optional[str] = None,
        api_key: Optional[str] = None,
        *,
        comp_id: Optional[str] = None,
        scene_id: Optional[str] = None,
        api_base: Optional[str] = None,
    ):
        self.is_server = get_is_server()
        if self.is_server:
            print("""
Warning: Running in server model!
This is not meant to be used outside of the ArenaX Labs benchmarking server.
Console interactions will be disabled, and the use of custom evaluation functions is forced to True. Which will skip the approval prompt.
            """)

        if self.is_server:
            self._log_capture = StringIO()
            self._original_stdout = sys.stdout
            sys.stdout = TeeIO(self._log_capture, sys.__stdout__)
        else:
            self._log_capture = None
            self._original_stdout = None
        self._console = SAIConsole()

        with self._console.status("Loading SAI CLI...") as status:
            self._api = APIClient(
                console=self._console,
                api_key=api_key,
                api_base=api_base,
            )

            self._package_control = PackageControl(
                api=self._api,
                console=self._console,
                is_disabled=self.is_server,
            )

            self._console.display_title(
                self._package_control._get_package_version("sai_rl") or "unknown",
                self._package_control._is_editable_install("sai_rl"),
            )

            self._package_control.setup(status)

            self._tasks: list[TaskType] = []
            self._scene: Optional[SceneType] = None
            self._environment: Optional[EnvironmentType] = None
            self._competition: Optional[CompetitionType] = None

            self._env = None

            self._console.print()

            if comp_id or env_id or scene_id:
                self._load_tasks(comp_id=comp_id, env_id=env_id, scene_id=scene_id, status=status)

            self._console.print()

    # ---- Internal Utility Methods ----
    def _check_setup(self) -> bool:
        if not self._package_control.setup_complete:
            raise SetupError("Setup not complete")
        assert self._package_control.setup_complete
        return True

    def _get_logs(self) -> str:
        if self._log_capture:
            return self._log_capture.getvalue()
        return ""

    # ---- Print Methods ----
    def _print_tasks(self, comp_bool):
        if not self._tasks:
            raise CompetitionError("No tasks loaded")

        table = Table(
            show_header=True,
            header_style="bold magenta",
            box=None,
            show_lines=False,
            expand=True,
            padding=(0, 2),
        )
        table.add_column("Task", style="bold cyan", justify="right", width=8)
        table.add_column("Environment", style="white", overflow="fold", min_width=40)
        table.add_column("Score Weight", style="white", justify="right", width=15)
        table.add_column("Episodes", style="green", justify="right", width=15)

        for idx, task in enumerate(self._tasks):
            env = task.environment
            env_name = getattr(env, "name", "Unknown")
            env_id = getattr(env, "gymId", "Unknown")

            n_benchmarks = getattr(task, "numberOfBenchmarks", None) or "-"

            env_desc = f"{env_name} [dim]({env_id})[/dim]"

            table.add_row(
                f"[bold]{idx}[/bold]",
                env_desc,
                str(task.scoreWeight),
                str(n_benchmarks),
            )

        panel = self._console.panel(
            Align.left(table),
            title=f"[b cyan]{'Competition' if comp_bool else 'Benchmark'} Tasks[/b cyan]",
            border_style="cyan",
            padding=(1, 1),
        )
        self._console.print(panel)

    def _print_submission_details(
        self,
        name: str,
        model_manager: ModelManager,
    ):
        if not self._competition and not self._environment:
            raise CompetitionError("No competition or environment loaded")

        title = f'"{name}" Submission Details'

        info_group = f"""[bold cyan]
Competition ID:[/bold cyan]      {self._competition.id}
[bold cyan]Competition Name:[/bold cyan]    {self._competition.name}
[bold cyan]Model Type:[/bold cyan]          {model_manager.model_type}
[bold cyan]Preprocess Function:[/bold cyan]  {"Custom" if model_manager._preprocess_manager else "Default (environment state)"}
[bold cyan]Action Function:[/bold cyan]  {"Custom" if model_manager._action_manager else f"Default ({'sample' if model_manager._handler.is_continuous else 'argmax'})"}"""

        submission_info = self._console.group(Align.left(Text.from_markup(info_group)))

        panel = self._console.panel(submission_info, title=title, padding=(0, 2))
        self._console.print(panel)

    # ---- Parse Methods ----
    def _get_task(self, task: Union[int, str, TaskType]) -> TaskType:
        if not self._tasks:
            raise CompetitionError("No tasks loaded")

        if isinstance(task, TaskType):
            return task

        if isinstance(task, str):
            env_id = task
            matches = [
                i
                for i, task in enumerate(self._tasks)
                if task.environment.gymId == env_id
            ]

            if not matches:
                raise CompetitionError(f"Environment {env_id} not found.")

            if len(matches) > 1:
                raise CompetitionError(
                    f"Multiple tasks found with environment ID '{env_id}'. Please specify by index."
                )

            task = matches[0]

        if task < 0 or task >= len(self._tasks):
            raise CompetitionError(
                f"Task index {task} is out of range. Must be between 0 and {len(self._tasks) - 1}."
            )

        task = self._tasks[task]

        if not task:
            raise CompetitionError("Task not found")

        return task

    # ---- Load Methods ----
    def _load_tasks_direct(
        self, tasks: list[TaskType], status: Optional[SAIStatus] = None
    ):
        if status:
            status.update("Loading tasks...")

        self._tasks = tasks

        for index, task in enumerate(self._tasks):
            task.index = index
            task.totalTaskCount = len(self._tasks)
            self._package_control.load(
                task.environment.package.name,
                task.environment.package.version,
                status=status,
            )

        return self._tasks

    def _load_tasks(
        self,
        comp_id: Optional[str] = None,
        env_id: Optional[str] = None,
        scene_id: Optional[str] = None,
        status: Optional[SAIStatus] = None,
    ):
        if status:
            status.update("Loading tasks...")

        self._competition = None
        self._environment = None
        self._tasks = []

        if comp_id and (env_id or scene_id):
            self._console.warning(
                "Both competition and environment/scene IDs provided. Only the competition will be loaded."
            )
            env_id = None
            scene_id = None

        if comp_id:
            self._competition = self._api.competition.get(comp_id)
            if not self._competition:
                raise CompetitionError("Competition not found")

            self._tasks = self._competition.tasks
            for index, task in enumerate(self._tasks):
                task.index = index
                task.totalTaskCount = len(self._tasks)

        if scene_id:
            self._scene = self._api.scene.get(scene_id)
            if not self._scene:
                raise SceneError("Scene not found")

            self._tasks = [
                TaskType(environment=env, index=index, totalTaskCount=len(self._scene.environments))
                for index, env in enumerate(self._scene.environments)
            ]

        if env_id:
            self._environment = self._api.environment.get(env_id)
            if not self._environment:
                raise EnvironmentError("Environment not found")

            self._tasks = [TaskType(environment=self._environment)]

        for task in self._tasks:
            self._package_control.load(
                task.environment.package.name,
                task.environment.package.version,
                status=status,
            )

        self._print_tasks(comp_id is not None)
        return self._tasks

    ############################################################
    # Public Methods
    ############################################################
    def load_competition(self, comp_id: str):
        """
        Loads a competition by its ID.

        Args:
            comp_id (str): Platform ID of the competition to load

        Returns:
            list[TaskType]: Loaded tasks for the competition

        Raises:
            CompetitionError: If competition cannot be loaded

        Examples:
            >>> client.load_competition("squid-hunt")
            >>> client.watch()  # Watch random agent
        """
        self._check_setup()

        with self._console.status(f"Loading competition {comp_id}...") as status:
            return self._load_tasks(comp_id=comp_id, status=status)

    def load_environment(self, env_id: str):
        """
        Loads an environment by its ID.

        Args:
            env_id (str): Platform ID of the environment to load

        Returns:
            list[TaskType]: Loaded tasks for the environment

        Raises:
            EnvironmentError: If environment cannot be loaded

        Examples:
            >>> client.load_environment("SquidHunt-v0")
            >>> client.watch()  # Watch random agent
        """
        self._check_setup()

        with self._console.status(f"Loading environment {env_id}...") as status:
            return self._load_tasks(env_id=env_id, status=status)

    def load_scene(self, scene_id: str):
        """
        Loads a scene by its ID.

        Args:
            scene_id (str): Platform ID of the scene to load

        Returns:
            list[TaskType]: Loaded tasks for the scene

        Raises:
            SceneError: If scene cannot be loaded

        Examples:
            >>> client.load_scene("robot-soccer")
            >>> client.watch()  # Watch random agent
        """
        self._check_setup()

        with self._console.status(f"Loading scene {scene_id}...") as status:
            return self._load_tasks(scene_id=scene_id, status=status)

    def reset(self):
        """
        Clears the currently loaded environment.

        This removes all references to the current environment, allowing
        you to load a different one or start fresh.

        Examples:
            >>> client.reset()
            >>> client.load_environment("new-env-id")
        """
        self._check_setup()

        self._competition = None
        self._environment = None
        self._tasks = []

        if self._env is not None:
            self._env.close()
            self._env = None

    def make_env(
        self,
        task_index: int | str = 0,
        render_mode: Literal["human", "rgb_array"] = None,
        use_custom_eval: bool = True,
        **kwargs,
    ):
        """
        Creates a new instance of the competition environment.

        Args:
            task_index (int): Index of the task to create, or ID of the environment to create.
            render_mode (Literal["human", "rgb_array"]): How to render the environment
                - "human": Display environment in a window
                - "rgb_array": Return RGB array for video recording
            use_custom_eval (bool): Whether to use custom evaluation function
                If True, uses the competition's evaluation function if available
                If False, uses the default environment rewards
                Note: This will not match the server's evaluation if False
            **kwargs: Additional keyword arguments to pass to the environment
                Note: These will be ignored when using a competition environment

        Returns:
            gym.Env: A Gymnasium environment instance

        Raises:
            CompetitionError: If no competition or environment is loaded

        Examples:
            >>> env = client.make_env()
            >>> obs, _ = env.reset()
            >>> env.render()

            >>> # With custom environment args (only works for non-competition environments)
            >>> env = client.make_env(truncate_episode_steps=100)
        """
        self._check_setup()
        task = self._get_task(task_index)

        self._env = make_env(
            task=task,
            use_custom_eval=use_custom_eval,
            competition_id=self._competition.id if self._competition else None,
            console=self._console,
            render_mode=render_mode,
            **kwargs,
        )

        return self._env

    def watch(
        self,
        model: Optional[ModelType] = None,
        action_function: Optional[str | Callable] = None,
        preprocessor_class: Optional[str | type] = None,
        *,
        task_indexes: list[int | str] = [],
        model_type: Optional[ModelLibraryType] = None,
        algorithm: Optional[str] = None,
        num_runs: int = 1,
        use_custom_eval: bool = True,
    ):
        """
        Watch a model (or random agent) interact with the environment.

        Args:
            model (Optional[ModelType]): Model to watch. Can be one of:
                - PyTorch model (torch.nn.Module)
                - TensorFlow model (tf.Module or tensorflow.compat.v1)
                - Keras model (tf.keras.Model)
                - Stable-Baselines3 model (BaseAlgorithm)
                - ONNX model (OnnxAgentWrapper)
                - URL or file path (str)
                If None, uses random actions
            action_function (Optional[str | Callable]): Custom action function
                If provided, overrides the model's default action function
            preprocessor_class (Optional[str | type]): Custom preprocessor class
                If provided, adds a custom preprocessor to the model
            env_id (Optional[Union[str, list[str]]]): Environment ID(s) to watch.
            model_type (Optional[ModelLibraryType]): Framework used. One of:
                - "pytorch"
                - "tensorflow"
                - "keras"
                - "stable_baselines3"
                - "onnx"
            algorithm (Optional[str]): Algorithm used by the model, for Stable Baselines3 models.
            num_runs (int): Number of episodes to run (default: 1)
            use_custom_eval (bool): Whether to use custom evaluation function
                If True, uses the competition's evaluation function if available
                If False, uses the default environment rewards
                Note: This will not match the server's evaluation if False

        Raises:
            BenchmarkError: If watching fails
            EnvironmentError: If no competition is loaded

        Examples:
            >>> # Watch random agent
            >>> client.watch()
            >>>
            >>> # Watch PyTorch model
            >>> model = torch.load("model.pt")
            >>> client.watch(model=model, model_type="pytorch", num_runs=3)
        """
        self._check_setup()
        if not self._tasks:
            raise CompetitionError("No tasks loaded")

        tasks = [
            task
            for index, task in enumerate(self._tasks)
            if not task_indexes or index in task_indexes
        ]

        for task in tasks:
            self._single_watch(
                task=task,
                model=model,
                action_function=action_function,
                preprocessor_class=preprocessor_class,
                model_type=model_type,
                algorithm=algorithm,
                num_runs=num_runs,
                use_custom_eval=use_custom_eval,
            )

    def _single_watch(
        self,
        task: TaskType,
        model: Optional[ModelType] = None,
        action_function: Optional[str | Callable] = None,
        preprocessor_class: Optional[str | type] = None,
        *,
        model_type: Optional[ModelLibraryType] = None,
        algorithm: Optional[str] = None,
        num_runs: int = 1,
        use_custom_eval: bool = True,
    ):
        self._check_setup()

        env = None
        self._console.print()
        with self._console.status("Setting up environment...") as status:
            try:
                env = self.make_env(
                    task_index=task,
                    render_mode="human",
                    use_custom_eval=use_custom_eval,
                )

                if model is not None:
                    model_manager = ModelManager(
                        env=env,
                        model=model,
                        model_type=model_type,
                        algorithm=algorithm,
                        preprocessor_class=preprocessor_class,
                        action_function=action_function,
                        console=self._console,
                        status=status,
                    )
                    status.update(
                        f"Watching {model_manager.model_type} model in '{env.spec.id}' environment..."  # type: ignore
                    )
                else:
                    model_manager = None
                    status.update(
                        f"Watching random agent in '{env.spec.id}' environment..."  # type: ignore
                    )

                self._console.print()

                for run_index in range(num_runs):
                    self._console.info(
                        f"Running watch {run_index + 1} of {num_runs}..."
                    )

                    obs, info = env.reset()
                    terminated = False
                    truncated = False
                    scores = 0
                    timesteps = 0

                    while not terminated and not truncated:
                        if model_manager:
                            action = model_manager.get_action(obs, info)[0]
                        else:
                            action = env.action_space.sample()

                        obs, reward, terminated, truncated, info = env.step(action)
                        env.render()

                        scores += reward  # type: ignore
                        timesteps += 1

                    env.close()

                    self._console.success(
                        f"Episode finished after {timesteps} timesteps with score: {scores}"
                    )

                self._console.print()

            except Exception as e:
                self._console.error(f"Unable to watch model: {e}")
                raise BenchmarkError(e)

            finally:
                if env:
                    env.close()

    def evaluate(
        self,
        model: Optional[ModelType] = None,
        action_function: Optional[str | Callable] = None,
        preprocessor_class: Optional[str | type] = None,
        *,
        task_indexes: list[int | str] = [],
        model_type: Optional[ModelLibraryType] = None,
        algorithm: Optional[str] = None,
        num_envs: Optional[int] = None,
        video_dir: Optional[str] = None,
        show_progress: bool = True,
        throw_errors: bool = True,
        timeout: int = 600,
        use_custom_eval: bool = True,
    ) -> BenchmarkResult:
        """
        New preferred method for running benchmarks.
        """
        return self.benchmark(
            model=model,
            action_function=action_function,
            preprocessor_class=preprocessor_class,
            task_indexes=task_indexes,
            model_type=model_type,
            algorithm=algorithm,
            num_envs=num_envs,
            video_dir=video_dir,
            show_progress=show_progress,
            throw_errors=throw_errors,
            timeout=timeout,
            use_custom_eval=use_custom_eval,
        )

    def benchmark(
        self,
        model: Optional[ModelType] = None,
        action_function: Optional[str | Callable] = None,
        preprocessor_class: Optional[str | type] = None,
        *,
        task_indexes: list[int | str] = [],
        model_type: Optional[ModelLibraryType] = None,
        algorithm: Optional[str] = None,
        num_envs: Optional[int] = None,
        video_dir: Optional[str] = None,
        show_progress: bool = True,
        throw_errors: bool = True,
        timeout: int = 600,
        use_custom_eval: bool = True,
    ) -> BenchmarkResult:
        """
        Run benchmark evaluation of a model.

        Args:
            model (Optional[ModelType]): Model to evaluate. Can be one of:
                - PyTorch model (torch.nn.Module)
                - TensorFlow model (tf.Module or tensorflow.compat.v1)
                - Keras model (tf.keras.Model)
                - Stable-Baselines3 model (BaseAlgorithm)
                - ONNX model (onnxruntime.InferenceSession)
                - URL or file path (str)
                If None, uses random actions
            action_function (Optional[str | Callable]): Custom action function
                If provided, overrides the model's action function
            preprocessor_class (Optional[str | type]): Custom preprocessor class
                If provided, overrides the model's preprocessor
            model_type (Optional[ModelLibraryType]): Framework used. One of:
                - "pytorch"
                - "tensorflow"
                - "keras"
                - "stable_baselines3"
                - "onnx"
            algorithm (Optional[str]): Algorithm used by the model, for Stable Baselines3 models.
            num_envs (Optional[int]): Number of environments to run in parallel
                If None, uses the competition's number of benchmarks if available
                Defaults to 1
            video_dir (Optional[str]): Path to save video recording
                If None, no video is recorded
            show_progress (bool): Whether to show progress bar during benchmark
                Defaults to True
            throw_errors (bool): Whether to raise exceptions on errors
                If False, returns error in results instead
                Defaults to True
            timeout (int): Maximum time in seconds to run the benchmark
                Defaults to 600 seconds (10 minutes)
            use_custom_eval (bool): Whether to use custom evaluation function
                If True, uses the competition's evaluation function if available
                If False, uses the default environment rewards
                Note: This will not match the server's evaluation if False

        Returns:
            BenchmarkResult: Results for the benchmark

        Examples:
            >>> # Benchmark random agent
            >>> results = client.benchmark()
            >>> print(f"Score: {results['score']}")
            >>>
            >>> # Benchmark PyTorch model with video
            >>> model = torch.load("model.pt")
            >>> results = client.benchmark(
            ...     model=model,
            ...     model_type="pytorch",
            ...     video_path="benchmark.mp4"
            ... )
        """
        self._console.warning(
            "The 'benchmark' method is deprecated and will be removed in a future release. Use 'evaluate' instead."
        )

        self._check_setup()

        start_time = time.time()
        results: BenchmarkResult = {
            "status": "error",
            "score": None,
            "duration": 0,
            "tasks": [],
            "error": None,
        }
        error = None

        try:
            if not self._tasks:
                raise CompetitionError(
                    "No tasks loaded. Load a competition or environment first, e.g. SAIClient(comp_id='...') or client.load_environment('...')."
                )

            tasks = [
                task
                for index, task in enumerate(self._tasks)
                if not task_indexes or index in task_indexes
            ]
            if not tasks:
                raise CompetitionError(
                    "No matching tasks for the provided 'task_indexes'. Use indexes from the 'Loaded Tasks' table or leave empty to run all."
                )

            if num_envs is not None and num_envs <= 0:
                self._console.warning(
                    "num_envs must be > 0. Falling back to 1 environment."
                )
                num_envs = 1

            tasks_results = []
            for task in tasks:
                task_result = self._single_benchmark(
                    task=task,
                    model=model,
                    action_function=action_function,
                    preprocessor_class=preprocessor_class,
                    model_type=model_type,
                    algorithm=algorithm,
                    num_envs=num_envs,
                    video_dir=video_dir,
                    show_progress=show_progress,
                    timeout=timeout,
                    use_custom_eval=use_custom_eval,
                )
                tasks_results.append(task_result)

            results["status"] = "success"
            total_weighted_score = sum(
                task_result["score"] * task.scoreWeight
                for task_result, task in zip(tasks_results, tasks)
            )
            total_weight = sum(task.scoreWeight for task in tasks)
            results["score"] = (
                total_weighted_score / total_weight if total_weight > 0 else 0
            )
            results["tasks"] = tasks_results

        except (ModelError, CustomCodeError) as e:
            error = e
            results["status"] = "error"
            results["error"] = str(e)

        except (CompetitionError, EnvironmentError, InternalError) as e:
            results["status"] = "failed"
            results["error"] = str(e)
            error = e

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            error = e

        finally:
            results["duration"] = time.time() - start_time

            if error and throw_errors:
                raise error

            if self._log_capture:
                results["logs"] = self._get_logs()

            return results

    def _single_benchmark(
        self,
        task: TaskType,
        model: Optional[ModelType] = None,
        action_function: Optional[str | Callable] = None,
        preprocessor_class: Optional[str | type] = None,
        model_type: Optional[ModelLibraryType] = None,
        algorithm: Optional[str] = None,
        num_envs: Optional[int] = None,
        video_dir: Optional[str] = None,
        show_progress: bool = True,
        timeout: int = 600,
        use_custom_eval: bool = True,
    ) -> BenchmarkTask:
        self._console.print()

        start_time = time.time()
        results: BenchmarkTask = {
            "id": task.id,
            "status": "error",
            "score": None,
            "duration": 0,
            "episodes": [],
        }

        env = None
        with self._console.status("Setting up benchmark...") as status:
            try:
                self._check_setup()
                status.update("Setting up environment...")

                env = None
                self._env = None
                kwargs = {}
                if self._competition is not None:
                    kwargs["competition_id"] = self._competition.id

                env_factory = make_env_factory(
                    task=task, 
                    use_custom_eval=use_custom_eval, 
                    console=self._console, 
                    **kwargs
                )

                env = env_factory()

                if env is None:
                    raise EnvironmentError("Environment not loaded")

                get_actions = None
                model_manager = None
                if model is not None:
                    model_manager = ModelManager(
                        console=self._console,
                        env=env,
                        model=model,
                        model_type=model_type,
                        algorithm=algorithm,
                        preprocessor_class=preprocessor_class,
                        action_function=action_function,
                        status=status,
                    )

                    def get_actions(obs, info={}):
                        return model_manager.get_action(obs, info)
                else:
                    self._console.warning("No model provided. Using random actions.")

                self._console.print()
                env.close()

                env = None
                self._env = None

                episodes, actions, seeds = run_benchmark(
                    env_creator=env_factory,
                    get_actions=get_actions,
                    console=self._console,
                    seed=task.seed,
                    num_envs=num_envs or task.numberOfBenchmarks,
                    status=status,
                    show_progress=show_progress,
                    save_actions=video_dir is not None,
                    timeout=timeout,
                )

                if seeds and video_dir:
                    scores = {
                        seed: episodes[i]["score"] for i, seed in enumerate(seeds)
                    }

                    # Check if all scores are the same
                    unique_scores = set(scores.values())

                    seeds_to_record = {}
                    if len(unique_scores) == 1:
                        # All scores are identical - just pick different seeds for variety
                        seed_list = list(scores.keys())
                        seeds_to_record = {
                            "best": seed_list[0],
                            "worst": seed_list[min(1, len(seed_list) - 1)],
                            "average": seed_list[min(2, len(seed_list) - 1)],
                        }
                    else:
                        best_seed, _ = max(scores.items(), key=lambda x: x[1])
                        worst_seed, _ = min(scores.items(), key=lambda x: x[1])

                        # Find average score seed that's different from best and worst
                        used_seeds = {best_seed, worst_seed}
                        remaining_scores = [
                            (seed, score)
                            for seed, score in scores.items()
                            if seed not in used_seeds
                        ]

                        avg_score = sum(scores.values()) / len(scores)
                        average_seed, _ = min(
                            remaining_scores, key=lambda x: abs(x[1] - avg_score)
                        )

                        seeds_to_record = {
                            "best": best_seed,
                            "worst": worst_seed,
                            "average": average_seed,
                        }

                    episodes_to_record: list[EpisodeType] = []
                    for label, seed in seeds_to_record.items():
                        match_index = seeds.index(seed)
                        videoKey = f"{task.id}/{label}.mp4"
                        episodes[match_index]["videoKey"] = videoKey
                        episodes_to_record.append(
                            EpisodeType(
                                seed=seed,
                                actions=actions[match_index],
                                output_path=str((Path(video_dir) / videoKey).resolve()),
                            )
                        )

                    if not os.path.exists(video_dir):
                        os.makedirs(video_dir)

                    record_episodes(
                        env_creator=env_factory,  # type: ignore
                        episodes=episodes_to_record,
                    )

                results["status"] = "success"
                results["episodes"] = episodes
                results["score"] = sum(
                    episodes[i]["score"] for i in range(len(episodes))
                ) / len(episodes)

                self._console.print()
                self._console.debug(
                    f"\n[bold]Results:[/bold]\n{json.dumps(results, indent=2)}"
                )

                if results["status"] == "success":
                    self._console.success("Evaluation completed successfully")

            except Exception as e:
                raise e

            finally:
                results["duration"] = time.time() - start_time

                if env:
                    env.close()

        self._console.print()
        return results

    # ---- Model Methods ----
    def submit_model(
        self,
        name: str,
        model: ModelType,
        action_function: Optional[str | Callable] = None,
        preprocessor_class: Optional[str | type] = None,
        *,
        model_type: Optional[ModelLibraryType] = None,
        algorithm: Optional[str] = None,
        use_onnx: bool = False,
        tag: str = "default",
    ):
        return self.submit(
            name=name,
            model=model,
            action_function=action_function,
            preprocessor_class=preprocessor_class,
            model_type=model_type,
            algorithm=algorithm,
            use_onnx=use_onnx,
            tag=tag,
        )

    def submit(
        self,
        name: str,
        model: ModelType,
        action_function: Optional[str | Callable] = None,
        preprocessor_class: Optional[str | type] = None,
        *,
        model_type: Optional[ModelLibraryType] = None,
        algorithm: Optional[str] = None,
        use_onnx: bool = False,
        tag: str = "default",
    ):
        """
        Submits a model to the current competition.

        Args:
            name (str): Name for the submission
            model (ModelType): Model to submit. Can be one of:
                - PyTorch model (torch.nn.Module)
                - TensorFlow model (tf.Module or tensorflow.compat.v1)
                - Keras model (tf.keras.Model)
                - Stable-Baselines3 model (BaseAlgorithm)
                - ONNX model (OnnxAgentWrapper)
                - URL or file path (str)
            model_type (Optional[ModelLibraryType]): Framework used. One of:
                - "pytorch" - For PyTorch models
                - "tensorflow" - For TensorFlow v1 and v2 models
                - "keras" - For Keras models
                - "stable_baselines3" - For Stable-Baselines3 models
                - "onnx" - For ONNX models
            preprocessor_class (Optional[str | type]): Preprocess class code
            action_function (Optional[str | Callable]): Action function code
            use_onnx (bool): Whether to convert the model to ONNX format before submission
            skip_warning (bool): Skip validation warnings related to action function configuration

        Returns:
            dict: Submission information including:
                - id: Unique submission ID
                - name: Submission name
                - type: Model framework type
                - status: Current submission status
                - created_at: Timestamp of submission
                - updated_at: Timestamp of last update

        Raises:
            SubmissionError: If submission fails validation checks or upload fails
            CompetitionError: If no competition is currently loaded
            ValueError: If model type is invalid or incompatible with provided model

        Examples:
            >>> # Submit PyTorch model
            >>> model = torch.load("model.pt")
            >>> result = client.submit_model(
            ...     name="My Model v1",
            ...     model=model,
            ...     model_type="pytorch"
            ... )
            >>>
            >>> # Submit with action function and ONNX conversion
            >>> def action_fn(policy):
            ...     return np.argmax(policy, axis=1)
            >>>
            >>> result = client.submit_model(
            ...     name="My Model v2",
            ...     model=model,
            ...     model_type="pytorch",
            ...     action_function=action_fn,
            ...     use_onnx=True
            ... )
        """
        self._check_setup()

        if not self._api.api_key:
            raise AuthenticationError(
                "No API key provided.\n\nPlease run 'sai login' to authenticate with your user.\n"
            )

        if not self._competition:
            raise CompetitionError(
                "No competition is loaded, please load a competition first using SAIClient(competition_id='')"
            )

        if getattr(self._competition, "opensource", False):
            raise SubmissionError(
                "Cannot use python to submit to an open source competition. Please submit through the SAI website."
            )

        with self._console.status("Submitting model to the competition...") as status:
            env = make_env(task=self._get_task(0), console=self._console, competition_id=self._competition.id)

            model_manager = ModelManager(
                console=self._console,
                env=env,
                model=model,
                model_type=model_type,
                algorithm=algorithm,
                preprocessor_class=preprocessor_class,
                action_function=action_function,
            )

            self._console.print()

            self._print_submission_details(
                name,
                model_manager,  # use_onnx, action_function
            )

            file_extension = {
                "stable_baselines3": ".zip",
                "pytorch": ".pt",
                "tensorflow": ".pb",
                "keras": ".keras",
                "onnx": ".onnx",
            }.get("onnx" if use_onnx else model_manager.model_type, "")

            isTensorflowV2 = False
            if model_manager.model_type == "tensorflow" and not use_onnx:
                isTensorflowV2 = model_manager._handler.is_tf2_model(model)

            random_id = "".join(
                random.choices(string.ascii_lowercase + string.digits, k=6)
            )
            os.makedirs(config.temp_path, exist_ok=True)
            temp_model_path = f"{config.temp_path}/{random_id}{file_extension if not isTensorflowV2 else ''}"
            model_manager.save_model(temp_model_path, use_onnx=use_onnx)

            if preprocessor_class:
                temp_preprocess_code_path = (
                    f"{config.temp_path}/preprocess_{random_id}.py"
                )
                model_manager.save_preprocess_code(temp_preprocess_code_path)

            if action_function:
                temp_action_fn_path = f"{config.temp_path}/action_{random_id}.py"
                model_manager.save_action_function(temp_action_fn_path)

            status.update("Creating submission...")

            adj_temp_model_path = (
                f"{temp_model_path}{'/saved_model.pb' if isTensorflowV2 else ''}"
            )
            files = {
                "model": (
                    os.path.basename(adj_temp_model_path),
                    open(adj_temp_model_path, "rb"),
                    "application/octet-stream",
                ),
            }

            if preprocessor_class:
                files["preprocessCode"] = (
                    os.path.basename(temp_preprocess_code_path),
                    open(temp_preprocess_code_path, "rb"),
                    "text/plain",
                )

            if action_function:
                files["actionFunction"] = (
                    os.path.basename(temp_action_fn_path),
                    open(temp_action_fn_path, "rb"),
                    "text/plain",
                )

            is_submission_success = False
            try:
                is_submission_success = self._api.submission.create(
                    {
                        "name": name,
                        "type": model_manager.model_type,
                        "competitionId": (
                            getattr(self._competition, "id", None)
                            or (
                                self._competition["id"]
                                if isinstance(self._competition, dict)
                                else None
                            )
                        ),
                        "algorithm": model_manager.algorithm,
                        "method": "python",
                        "tag": tag,
                    },
                    files=files,
                )
            finally:
                for file_tuple in files.values():
                    file_tuple[1].close()

            if not is_submission_success:
                raise SubmissionError("Failed to create submission")

            if os.path.exists(temp_model_path):
                if isTensorflowV2 and os.path.isdir(temp_model_path):
                    shutil.rmtree(temp_model_path)  # remove directory
                else:
                    os.remove(temp_model_path)  # remove file
            else:
                self._console.warning("Temporary model file not found.")

            self._console.success("Model submitted successfully.")

            return is_submission_success

    def check_model_compliance(self, env, model: ModelType):
        model_manager = ModelManager(env, model)
        compliant = model_manager.check_compliance()
        if compliant:
            print("Your model is compliant with SAI submissions ✅")
        else:
            print("Your model is NOT compliant with SAI submissions ❌")
        return compliant

    def save_model(
        self,
        name: str,
        model: ModelType,
        model_type: Optional[ModelLibraryType] = None,
        algorithm: Optional[str] = None,
        use_onnx: bool = False,
        output_path: str = "./",
    ):
        """
        Saves a model to disk in the appropriate format.

        Args:
            name (str): Name for the saved model file (without extension)
            model (ModelType): Model to save. Can be one of:
                - PyTorch model (torch.nn.Module)
                - TensorFlow model (tf.Module or tensorflow.compat.v1)
                - Keras model (tf.keras.Model)
                - Stable-Baselines3 model (BaseAlgorithm)
                - ONNX model (OnnxAgentWrapper)
                - URL or file path (str)
            model_type (Optional[ModelLibraryType]): Framework used. One of:
                - "pytorch" (.pt)
                - "tensorflow" (.pb)
                - "keras" (.keras)
                - "stable_baselines3" (.zip)
                - "onnx" (.onnx)
            use_onnx (bool): Whether to convert and save model in ONNX format (default: False)
            output_path (str): Directory to save the model file (default: "./")

        Returns:
            str: Full path to the saved model file

        Raises:
            ModelError: If model cannot be saved or converted to ONNX
            CompetitionError: If no competition is loaded

        Note:
            - File extension is automatically added based on model_type
            - If use_onnx=True, model will be converted and saved in ONNX format regardless of original type

        Examples:
            >>> # Save PyTorch model
            >>> model = torch.load("model.pt")
            >>> path = client.save_model(
            ...     name="my_model",
            ...     model=model,
            ...     model_type="pytorch",
            ...     output_path="./models"
            ... )  # Saves to ./models/my_model.pt
            >>> print(path)
            './models/my_model.pt'

            >>> # Save model in ONNX format
            >>> path = client.save_model(
            ...     name="my_model",
            ...     model=model,
            ...     model_type="pytorch",
            ...     use_onnx=True,
            ...     output_path="./models"
            ... )  # Saves to ./models/my_model.onnx
        """
        self._check_setup()
        self._console.print()

        with self._console.status("Setting up model...") as status:
            env = self.make_env()

            model_manager = ModelManager(
                console=self._console,
                env=env,
                model=model,
                model_type=model_type,
                algorithm=algorithm,
            )

            file_extension = {
                "stable_baselines3": ".zip",
                "pytorch": ".pt",
                "tensorflow": ".pb",
                "keras": ".keras",
                "onnx": ".onnx",
            }.get("onnx" if use_onnx else model_manager.model_type, "")

            save_path = f"{output_path}/{name}{file_extension}"
            os.makedirs(output_path, exist_ok=True)

            status.update("Saving model...")
            model_manager.save_model(save_path, use_onnx=use_onnx)

            self._console.success(f"Model saved to {save_path}")

        return save_path

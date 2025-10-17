from typing import Literal, Optional, Callable

import os
import re
import inspect

import numpy as np
import gymnasium as gym

from rich.syntax import Syntax

from sai_rl.sai_console import SAIConsole, SAIStatus
from sai_rl.error import CustomCodeError


class CustomCodeManager:
    _console: Optional[SAIConsole]
    _env: Optional[gym.Env]

    def __init__(
        self,
        code: Optional[str | Callable] = None,
        name: str = "custom",
        code_type: Literal["function", "class"] = "function",
        env: Optional[gym.Env] = None,
        verbose: bool = False,
        console: Optional[SAIConsole] = None,
        status: Optional[SAIStatus] = None,
    ):
        self.name = f"{name} {code_type}"
        self._console = console
        self._env = env

        self._code = None
        self._code_source = None

        self.verbose = verbose

        self._path = None

        if status:
            status.update(f"Loading {name} {code_type}...")

        self.load(code, status)

    def _print(self):
        if not self._code_source:
            return

        if not self._console:
            return

        panel_group = self._console.group(
            Syntax(self._code_source, "python", theme="github-dark"),
        )

        panel = self._console.panel(
            panel_group,
            title=f"{self.name.capitalize()}",
            padding=(1, 2),
        )

        self._console.print()
        self._console.print(panel)

    def _load_from_code(self, code: str, status: Optional[SAIStatus] = None):
        if status:
            status.update(f"Loading {self.name} from code...")

        clean_code = self.remove_imports(code)

        object_name = None
        object_type = None
        for line in clean_code.splitlines():
            line = line.strip()
            if line.startswith("def "):
                object_name = line.split("def ")[1].split("(")[0].strip()
                object_type = "function"
                break
            elif line.startswith("class "):
                object_name = (
                    line.split("class ")[1].split("(")[0].split(":")[0].strip()
                )
                object_type = "class"
                break

        if not object_name or not object_type:
            raise CustomCodeError(
                "No function or class definition found in the provided code"
            )

        namespace = dict({"np": np, "env": self._env})
        exec(clean_code, namespace)

        loaded_object = namespace[object_name]
        if object_type == "class":
            self._code = loaded_object()
        else:
            self._code = loaded_object

        self._code_source = clean_code

    def _load_from_file(self, path: str, status: Optional[SAIStatus] = None):
        if status:
            status.update(f"Loading {self.name} from file...")

        self._path = path
        if not os.path.exists(path):
            raise CustomCodeError(f"File not found: {path}")

        with open(path, "r") as f:
            code = f.read()
            self._load_from_code(code)

    @staticmethod
    def remove_imports(code_string: str) -> str:
        """Remove import statements from code for security."""
        pattern = re.compile(
            r"^\s*#?\s*(from\s+\w+\s+import\s+.*|import\s+\w+.*|from\s+\w+\s+import\s+\(.*\)|import\s+\(.*\))",
            re.MULTILINE,
        )
        return re.sub(pattern, "", code_string)

    def has_method(self, method_name: str) -> bool:
        return hasattr(self._code, method_name) and callable(
            getattr(self._code, method_name)
        )

    def load(
        self,
        custom_code: Optional[str | Callable] = None,
        status: Optional[SAIStatus] = None,
    ):
        if status:
            status.update(f"Loading {self.name}...")

        if not custom_code:
            if self._console:
                self._console.warning(f"No {self.name} provided, skipping load.")
            return

        if isinstance(custom_code, str):
            if custom_code.startswith(("http://", "https://")):
                # Deprecating loading via internet. This was only really used by our benchmarking server,
                # however could potentially make users vulnerable to downloading and running arbitrary code.
                # Better to be safe here.
                raise CustomCodeError(
                    f"Could not load {self.name}. We no longer support loading custom code from the internet. "
                    "Please download it locally and use the file path instead."
                )
            elif custom_code.endswith(".py") and os.path.exists(custom_code):
                self._load_from_file(custom_code, status)
            elif custom_code.startswith(("def ", "class ")):
                self._load_from_code(custom_code, status)
            else:
                raise CustomCodeError(f"Unsupported {self.name} path: {custom_code}")
        elif callable(custom_code):
            custom_code_source = inspect.getsource(custom_code)
            self._load_from_code(custom_code_source)
        else:
            raise CustomCodeError(f"Unsupported {self.name} type: {type(custom_code)}")

        if self.verbose:
            self._print()

        if self._console:
            self._console.success(f"Successfully loaded {self.name}.")

    def save_code(self, path: str):
        if not self._code_source:
            raise CustomCodeError(f"No {self.name} loaded")

        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path), exist_ok=True)

        if os.path.exists(path):
            raise CustomCodeError(f"File already exists: {path}")

        if not path.endswith(".py"):
            raise CustomCodeError("File must end with .py")

        with open(path, "w") as f:
            f.write(self._code_source)
        self._path = path

    def clean(self):
        if self._path and os.path.exists(self._path):
            os.remove(self._path)
            self._path = None
        self._code = None
        self._code_source = None

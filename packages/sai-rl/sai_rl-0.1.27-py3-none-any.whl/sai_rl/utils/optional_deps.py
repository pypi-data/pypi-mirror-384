from importlib import import_module
from typing import Any, Iterable, Optional, Tuple

PROJECT_NAME = "sai-rl"


class OptionalDependencyError(ImportError):
    pass


def require(module: str, extra: str, import_name: Optional[str] = None) -> Any:
    """Import a module lazily, raising a helpful message that points to the
    correct extras group if it is missing.

    - module: human-friendly module label for the error message
    - extra: extras group name from pyproject optional-dependencies
    - import_name: dotted import path to actually import (defaults to module)
    """
    name = import_name or module
    try:
        return import_module(name)
    except Exception as exc:
        raise OptionalDependencyError(
            f"{module} is not installed. Install it with 'pip install \"{PROJECT_NAME}[{extra}]\"'."
        ) from exc


def require_many(specs: Iterable[Tuple[str, str, Optional[str]]]) -> Tuple[Any, ...]:
    """Import multiple modules with extras-aware errors.

    specs: iterable of (module_label, extras_group, import_name)
    """
    return tuple(require(mod, extra, import_name) for mod, extra, import_name in specs)

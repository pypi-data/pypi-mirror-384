from importlib import util
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class BaseEnv[ObsType: Any, ActType: Any](Protocol):
    """A gymnasium compatible environment protocol."""

    action_space: Any
    observation_space: Any

    def __init__(self, **kwargs: Any) -> None: ...

    def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None) -> tuple[ObsType, dict]: ...

    def step(self, action: ActType) -> tuple[ObsType, float, bool, bool, dict]: ...

    def get_success(self) -> bool: ...


def load_env_class_from_file(file: str, class_name: str = "Env") -> type[Any]:
    """Load an environment class from a Python file.

    Args:
        file: Path to Python file containing environment class
        class_name: Name of environment class in the file (default: "Env")

    Returns:
        The environment class

    Raises:
        AttributeError: If the class doesn't exist in the module
    """
    spec = util.spec_from_file_location("env_module", file)
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load module from {file}")

    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    if not hasattr(mod, class_name):
        raise AttributeError(f"Module {file} does not have class '{class_name}'")

    return getattr(mod, class_name)

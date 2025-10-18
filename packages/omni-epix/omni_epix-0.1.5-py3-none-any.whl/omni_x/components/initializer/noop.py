from dataclasses import dataclass

from omni_x.core import Run, Task, TaskInitializer


class NoopInitializer(TaskInitializer):
    """Initializer that assigns no parents (useful for ablations without archive)."""

    @dataclass(frozen=True)
    class Config:
        pass

    def __init__(self, config: Config) -> None:
        self.config = config

    def __call__(self, run: Run, task: Task) -> None:
        task.parents = []
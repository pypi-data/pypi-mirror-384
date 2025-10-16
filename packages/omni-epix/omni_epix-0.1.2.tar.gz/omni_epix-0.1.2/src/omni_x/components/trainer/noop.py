from dataclasses import dataclass

from omni_x.core import Run, Task, Trainer


class NoopTrainer(Trainer):
    """Dummy trainer that does no actual training, just sets a dummy checkpoint."""

    @dataclass(frozen=True)
    class Config:
        pass

    def __init__(self, config: Config) -> None:
        self.config = config

    def __call__(self, run: Run, task: Task) -> None:
        task.trained = True


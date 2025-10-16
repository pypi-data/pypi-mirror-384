import random
from dataclasses import dataclass

from omni_x.core import Evaluator, Run, Task


class RandomEvaluator(Evaluator):
    """Dummy evaluator that randomly marks tasks as successful based on a probability."""

    @dataclass(frozen=True)
    class Config:
        success_probability: float

    def __init__(self, config: Config) -> None:
        self.config = config

    def __call__(self, run: Run, task: Task) -> None:
        task.success = random.random() < self.config.success_probability


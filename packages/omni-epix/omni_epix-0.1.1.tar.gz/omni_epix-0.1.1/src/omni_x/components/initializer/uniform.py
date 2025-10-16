import random
from dataclasses import dataclass

from omni_x.core import Run, Task, TaskInitializer, log


class Uniform(TaskInitializer):
    """Assigns up to num_parents most similar tasks to a uniformly sampled query task, including the query task itself."""
    @dataclass(frozen=True)
    class Config:
        num_parents: int

    def __init__(self, config: Config) -> None:
        self.config = config

    def __call__(self, run: Run, task: Task) -> None:
        if len(run.archive) == 0:
            log("Archive is empty, no parents assigned", run=run, task=task)
            task.parents = []
            return

        idx = random.randint(0, len(run.archive)-1)
        sampled_task = run.archive.get(idx)
        tasks, sims = run.index.search(sampled_task.embedding_text, k=self.config.num_parents)
        log(f"Sampled task {idx}. Found neighbours {tasks} with similarities {sims}", run=run, task=task, step="sample_uniform")
        task.parents = tasks

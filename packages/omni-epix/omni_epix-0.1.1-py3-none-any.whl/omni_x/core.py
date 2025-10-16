from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterable, Iterator, NamedTuple, Protocol
from uuid import uuid4

from filelock import FileLock

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """"""

    id: str = field(default_factory=lambda: str(uuid4()))
    parents: list[int] | None = None  # archive indices of parent tasks
    description: str | None = None  # natural language description of the task
    code: str | None = None  # environment code (e.g. gym env, etc.)
    interesting: bool | None = None  # whether the task is rated interesting enough to pursue
    trained: bool | None = None  # how checkpoints are stored and utilized is up to the Trainer
    success: bool | None = None  # whether the trained model passed evaluation (successfully learned the task)
    archive_idx: int | None = None  # index in the archive, if archived
    done: bool = False  # whether the task has been fully processed (terminal state)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_archivable(self) -> bool:
        return not self.done and self.success is not None

    @property
    def is_discardable(self) -> bool:
        return self.done and self.success is None

    @property
    def embedding_text(self) -> str:
        """Text to be embedded for this task; Formatted as a python code file with a docstring."""
        assert self.description is not None and self.code is not None, "Embedding text needs task description and code"
        return f'"""\n{self.description.strip()}\n"""\n\n{self.code.strip()}\n'

    def __str__(self) -> str:
        return f"Task(id={self.id[:8]}, parents={[self.parents]}, description={self.description is not None}, code={self.code is not None}, interesting={self.interesting}, trained={self.trained is not None}, success={self.success}, archive_idx={self.archive_idx})"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        data = data.copy()
        return cls(**data)


class Archive(ABC):
    """"""

    @abstractmethod
    def __len__(self) -> int:
        """Number of archived tasks."""

    @abstractmethod
    def save(self, task: Task) -> None:
        """Save the current state of the task, overwriting any existing version."""

    @abstractmethod
    def get(self, id: str | int) -> Task:
        """Get a task by id or archive_idx"""

    @abstractmethod
    def get_archived(self) -> Iterable[Task]:
        """Get all archived tasks (i.e. saved tasks with "archivable" status), sorted by task.archive_idx."""

    @abstractmethod
    def get_discarded(self) -> Iterable[Task]:
        """Get all discarded tasks (i.e. saved tasks with "discarded" status), sorted by task.id alphabetically."""

    @abstractmethod
    def get_wip(self) -> Iterable[Task]:
        """Get all work-in-progress tasks (i.e. tasks not yet archived or discarded), sorted by task.id alphabetically."""


class TaskIndex(Protocol):
    @abstractmethod
    def add(self, task: Task) -> None:
        """Add a task to the index. The task must have an archive_idx."""

    @abstractmethod
    def search(self, query: str, k: int) -> tuple[list[int], list[float]]:
        """Returns the archive_idxs of the k most similar archived tasks and the similarity scores, including the query task itself if it is in the archive."""


@dataclass
class Run:
    name: str
    dir: Path
    archive: Archive
    index: TaskIndex
    pipeline: Iterable[Rule]
    config: DataclassInstance

    def add_to_archive(self, task: Task) -> None:
        if task.archive_idx is not None:
            log("Task already in archive, skipping add.", run=self, task=task, level=logging.WARNING)
            return
        assert task.is_archivable, "Only archivable tasks can be added to the archive"

        lock = FileLock(str(self.dir / ".archive.lock"))
        with lock:
            task.archive_idx = len(self.archive)
            self.archive.save(task)
            self.index.add(task)


class Rule(NamedTuple):
    name: str  # for logging
    predicate: Callable[[Task], bool]  # when to apply this rule
    fn: StepFn


class StepFn(Protocol):
    """A stage in the OMNI-EPIC pipeline that modifies the task in place."""

    def __call__(self, run: Run, task: Task) -> None: ...


class TaskInitializer(StepFn):
    """Initialize a new task with parents from the archive.

    Typically sets task.parents.
    """


class TaskGenerator(StepFn):
    """Generate a task description for a new interesting and learnable task, building on the given task's parents.

    Typically sets task.description.
    """


class EnvGenerator(StepFn):
    """Generate environment code for the given task.

    Typically sets task.code.
    """


class ModelOfInterestingness(StepFn):
    """Judge whether a task is interesting enough to pursue, comparing to similar tasks in the archive.

    Typically sets task.interesting.
    """


class Trainer(StepFn):
    """Train an agent on the given task.

    Typically sets task.trained.
    """


class Evaluator(StepFn):
    """Evaluate the trained agent to determine if it successfully completed the task.

    Typically sets task.success.
    """


class Reflector(StepFn):
    """Reflect on a failed task and modify the environment to make it more learnable.

    Typically modifies task.code.
    """


def create_default_omni_epic_pipeline(
    initializer: TaskInitializer,
    task_generator: TaskGenerator,
    env_generator: EnvGenerator,
    moi: ModelOfInterestingness,
    trainer: Trainer,
    evaluator: Evaluator,
    reflector: Reflector | None = None,
    max_reflect_attempts: int = 1,
) -> list[Rule]:
    """Standard OMNI-EPIC pipeline from the paper.

    Enforces field requirements via assertions (protocol "typically" statements become "must" for this pipeline).
    Custom pipelines can skip/add/rearrange - as long as tasks are eventually marked done.
    """

    def init_step(run: Run, task: Task) -> None:
        initializer(run, task)
        assert task.parents is not None, "Initializer must set task.parents"

    def gen_step(run: Run, task: Task) -> None:
        task_generator(run, task)
        assert task.description is not None, "Generator must set task.description"

    def env_step(run: Run, task: Task) -> None:
        env_generator(run, task)
        assert task.code is not None, "EnvGenerator must set task.code"

    def moi_step(run: Run, task: Task) -> None:
        moi(run, task)
        assert task.interesting is not None, "ModelOfInterestingness must set task.interesting"

    def train_step(run: Run, task: Task) -> None:
        trainer(run, task)
        assert task.trained is not None, "Trainer must set task.trained"

    def eval_step(run: Run, task: Task) -> None:
        evaluator(run, task)
        assert task.success is not None, "Evaluator must set task.success"

    def reflect_step(run: Run, task: Task) -> None:
        if reflector is None or task.metadata.get("reflect_attempts", 0) >= max_reflect_attempts:
            task.success = False
            return
        reflector(run, task)
        task.interesting = None
        task.trained = False
        task.metadata.setdefault("reflect_attempts", 0)
        task.metadata["reflect_attempts"] += 1

    def finalize_step(run: Run, task: Task) -> None:
        if task.is_archivable:
            log("Adding to archive.", run=run, task=task)
            run.add_to_archive(task)
        task.done = True

    rules = [
        Rule("initialize", lambda t: t.parents is None, init_step),
        Rule("generate_task", lambda t: t.description is None, gen_step),
        Rule("generate_env", lambda t: t.code is None, env_step),
        Rule("moi", lambda t: t.interesting is None, moi_step),
        Rule("train", lambda t: t.interesting is True and t.trained is None, train_step),
        Rule("evaluate", lambda t: t.trained is True and t.success is None, eval_step),
        *([Rule("reflect", lambda t: t.trained is True and t.success is False, reflect_step)] if reflector else []),
        Rule("finalize", lambda t: not t.done, finalize_step),
    ]

    return rules


def run_task(run: Run, task: Task) -> None:
    """Run one full task generation+evaluation loop, from sampling to saving to archive.
    If `task` is None, initialize a new task; otherwise continue the given task. Noop if the task is in a terminal state.
    """
    while not task.done:
        for name, predicate, fn in run.pipeline:
            if not predicate(task):
                continue
            t0 = time.time()
            log("Starting...", run=run, task=task, step=name)
            try:
                fn(run, task)
            except Exception as e:
                task.done = True
                task.metadata.setdefault("errors", []).append({"step": name, "msg": str(e), "time": time.time()})
                raise
            finally:
                dur = time.time() - t0
                task.metadata.setdefault("timings", []).append((name, dur))
                run.archive.save(task)
            log("Done.", run=run, task=task, dur=f"{dur:.2f}s", step=name)
            break
        else:
            raise ValueError(f"No applicable rule for task:\n{task}")


def sequential_runner(run: Run, resume: bool = False) -> Iterator[Task]:
    """Runs the OMNI-EPIC loop sequentially, yielding each completed task.
    If resume is True, on start continues any tasks in wip that are not yet archived or discarded.
    """
    to_resume: list[Task] = list(run.archive.get_wip()) if resume else []
    while True:
        task = Task() if not to_resume else to_resume.pop(0)
        run_task(run, task=task)
        yield task


def log(
    message: str, *, run: Run | None = None, task: Task | None = None, level: int = logging.INFO, **extra_parts: Any
) -> None:
    parts: dict[str, Any] = {}

    if run is not None:
        parts["run"] = run.name
    if task is not None:
        parts["task"] = task.id
    parts.update(extra_parts)

    segments = [f"[{time.strftime('%H:%M:%S', time.localtime())}]"]
    for key, value in parts.items():
        segments.append(f"[{key}:{value}]")
    prefix = "".join(segments)

    logger.log(level, f"{prefix} {message}")

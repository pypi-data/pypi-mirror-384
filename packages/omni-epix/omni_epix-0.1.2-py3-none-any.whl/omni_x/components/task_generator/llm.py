from dataclasses import dataclass

from omni_x.core import Run, Task, TaskGenerator
from omni_x.utils.llm.base import InstructorClient
from omni_x.utils.llm.logging import log_llm_call
from omni_x.utils.llm.prompts import TaskOutput, build_task_gen_messages


class LLMTaskGenerator(TaskGenerator):
    """Generate task descriptions using an LLM.

    Retrieves parent tasks, builds prompts, calls LLM, and updates the task.
    """

    @dataclass(frozen=True)
    class Config:
        substrate_description: str
        llm: InstructorClient.Config

    def __init__(self, config: Config) -> None:
        self.config = config
        self.client = InstructorClient(config.llm)

    def __call__(self, run: Run, task: Task) -> None:
        parents = [run.archive.get(idx) for idx in task.parents or []]
        messages = build_task_gen_messages(self.config.substrate_description, parents)

        result, completion = self.client.create_with_completion(response_model=TaskOutput, messages=messages)

        task.description = result.task

        metadata = log_llm_call(run.dir / "llm_logs", task.id, "task_generator", result=result, completion=completion)
        task.metadata.setdefault("llm_calls", []).append(metadata)

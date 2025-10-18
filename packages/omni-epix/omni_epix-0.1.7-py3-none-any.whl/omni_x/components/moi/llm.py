from dataclasses import dataclass

from omni_x.core import ModelOfInterestingness, Run, Task
from omni_x.utils.llm.base import InstructorClient
from omni_x.utils.llm.logging import log_llm_call
from omni_x.utils.llm.prompts import MoiOutput, build_moi_messages


class LLMMoi(ModelOfInterestingness):
    """Judge task interestingness using an LLM.

    Retrieves similar tasks, builds prompts, calls LLM, and updates the task.
    """

    @dataclass(frozen=True)
    class Config:
        num_similar: int
        llm: InstructorClient.Config

    def __init__(self, config: Config) -> None:
        self.config = config
        self.client = InstructorClient(config.llm)

    def __call__(self, run: Run, task: Task) -> None:
        similar_idxs, _ = run.index.search(task.embedding_text, k=self.config.num_similar)
        similar_tasks = [run.archive.get(idx) for idx in similar_idxs]

        messages = build_moi_messages(task, similar_tasks)

        result, completion = self.client.create_with_completion(response_model=MoiOutput, messages=messages)

        task.interesting = result.interesting

        metadata = log_llm_call(run.dir / "llm_logs", task.id, "moi", result=result, completion=completion)
        task.metadata.setdefault("llm_calls", []).append(metadata)

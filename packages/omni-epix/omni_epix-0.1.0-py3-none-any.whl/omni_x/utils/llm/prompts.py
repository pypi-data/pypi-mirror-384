"""Prompt utilities for OMNI-X components."""

from __future__ import annotations

from pydantic import BaseModel, Field
from openai.types.chat import ChatCompletionMessageParam

from omni_x.core import Task



class TaskOutput(BaseModel):
    """LLM output for task generation."""

    think: str | None = Field(None, description="Optional reasoning or rationale")
    task: str = Field(description="The task description")


class EnvOutput(BaseModel):
    """LLM output for environment generation."""

    think: str | None = Field(None, description="Optional reasoning or rationale")
    code: str = Field(description="Python code implementing the environment")


class MoiOutput(BaseModel):
    """LLM output for model of interestingness."""

    think: str | None = Field(None, description="Optional reasoning or rationale")
    interesting: bool = Field(description="Whether the task is interesting")


def format_tasks_xml(tasks: list[Task], language: str = "python") -> str:
    """Format tasks as XML with code in fenced blocks.
    Also add archive idx, which might help the llm identify tasks and skill progression, and is useful for debugging.
    """
    if not tasks:
        return ""
    parts = []
    for task in tasks:
        idx = task.archive_idx if task.archive_idx is not None else "?" # should alwys be set
        parts.append(f"<task idx='{idx}'>")
        parts.append(f"<description>{task.description}</description>")
        if task.code:
            parts.append("<code>")
            parts.append(f"```{language}")
            parts.append(task.code)
            parts.append("```")
            parts.append("</code>")
        parts.append("</task>")
    return "\n".join(parts)


def build_task_gen_messages(
    substrate_desc: str,
    parents: list[Task],
) -> list[ChatCompletionMessageParam]:
    successful = [t for t in parents if t.success is not None and t.success]
    failed = [t for t in parents if t.success is not None and not t.success]

    system_content = f"""You are an expert in curriculum learning and reinforcement learning.
Your goal is to help an agent master a diverse set of interesting tasks.

You will be provided with some tasks the agent has successfully learned and tasks it attempted but failed to learn.
Your objective is to decide the next task for the agent, selecting one that is learnable, interesting, and novel.

- The next task should be learnable:
    - Not too difficult for the agent to learn given its current skill set.
    - Realistic for the agent based on its description.
    - Possible to implement and complete given the environment description.
    - Don't suggest a task that builds on a past failed task.
- The next task should be interesting:
    - Novel and creative compared to the tasks the agent has already learned.
    - Useful according to humans, making it worth learning.
    - Fun or engaging to watch (IF applicable).
- Be specific in the task description:
    - State clearly what the task of the agent is.
    - Clearly define what the success condition is.
    - Clearly define what the different reward or penalty components are.
    - Clearly define what the termination conditions are.
- The task should not take too long to complete.
- Return only the task description, not the environment code.
- Ensure that the task poses no harm to humans and aligns with human values and ethics.

<substrate>
{substrate_desc}
</substrate>

Before you answer, think about promising tasks (tasks that meet the criteria), reason step-by-step about which one would be the most suitable, and how to formulate it effectively."""

    user_content = f"""<successful_tasks>
{format_tasks_xml(successful)}
</successful_tasks>

<failed_tasks>
{format_tasks_xml(failed)}
</failed_tasks>

Generate the next task for the agent."""

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def build_env_gen_messages(
    substrate_desc: str,
    task_description: str,
    example_tasks: list[Task] | None = None,
) -> list[ChatCompletionMessageParam]:
    system_content = f"""You are an expert in Python programming and reinforcement learning.
Your goal is to implement an environment in the format specified below, specifically designed to train an agent for a given task.
You will be provided with the task description and with some example tasks and their corresponding environment code.
Your objective is to write environment code that rigorously aligns with the task description, helping the agent learn the task as effectively as possible.
Avoid unnecessary complexity. Focus on implementing exactly what the task requires.

<substrate>
{substrate_desc}
</substrate>
Implement the environment code for this task."""

    user_content = f"""<example_tasks>
{format_tasks_xml(example_tasks or [])}
</example_tasks>

<target_task>
{task_description}
</target_task>
Generate the Python code implementing the environment for the target task."""

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def build_env_fix_messages(
    substrate_desc: str,
    task_description: str,
    previous_code: str,
    error_traceback: str,
    example_tasks: list[Task] | None = None,
) -> list[ChatCompletionMessageParam]:
    system_content = f"""You are an expert in Python programming and reinforcement learning.
Your goal is to fix environment implementation errors.
You will be provided with the task description, the previous code that failed, and the error traceback from running the code.
Your objective is to fix the errors in the code so that it runs successfully and implements the task correctly.

<substrate>
{substrate_desc}
</substrate>"""

    user_content = f"""<example_tasks>
{format_tasks_xml(example_tasks or [])}
</example_tasks>

<target_task>
{task_description}
</target_task>

<previous_code>
```python
{previous_code}
```
</previous_code>

<error>
{error_traceback}
</error>

Fix the errors in the code and generate corrected Python code implementing the environment for the target task."""

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def build_moi_messages(
    new_task: Task,
    similar_tasks: list[Task],
) -> list[ChatCompletionMessageParam]:
    """Build messages for model of interestingness."""
    system_content = """You are an expert in curriculum learning and reinforcement learning.
Your goal is to help an agent master a diverse set of interesting tasks.

You will be provided with a list of existing tasks and a new proposed task.
Your objective is to determine whether the new task is interesting enough to pursue.

The new task is interesting if it is:
- Novel compared to existing tasks, to build a diverse skill set
- Creative or surprising
- Not too easy given the agent's current capabilities, progressing toward more complex challenges
- Useful according to humans, making it worth learning
- Fun or engaging to watch (IF applicable).

Before you answer, briefly think about the new task, reason step-by-step about whether it meets the criteria for being interesting, and then give your final answer.
"""

    user_content = f"""<existing_tasks>
{format_tasks_xml(similar_tasks)}
</existing_tasks>

<new_task>
{format_tasks_xml([new_task])}
</new_task>

Is this new task interesting compared to the existing tasks?"""

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from openai.types.chat import ChatCompletion


def log_llm_call(
    log_dir: Path,
    task_id: str,
    step: str,
    result: BaseModel,
    completion: ChatCompletion,
) -> dict[str, Any]:
    """Save full LLM call to disk and return metadata summary.

    Args:
        run_dir: Run directory
        task_id: Task ID
        step: Pipeline step name
        result: Parsed result object
        completion: Full LLM completion object
    """
    log_dir.mkdir(exist_ok=True, parents=True)
    timestamp = time.time()
    log_file = log_dir / f"{task_id}_{step}_{int(timestamp)}.json"
    log_file.write_text(
        json.dumps(
            {
                "timestamp": timestamp,
                "task_id": task_id,
                "step": step,
                "completion": completion.model_dump(),
                "parsed_result": result.model_dump(),
            },
            indent=2,
            default=str,
        )
    )
    usage = completion.usage
    metadata: dict[str, Any] = {
        "timestamp": timestamp,
        "step": step,
        "model": completion.model,
        "input_tokens": usage.prompt_tokens if usage else None,
        "output_tokens": usage.completion_tokens if usage else None,
        "log_file": str(log_file.relative_to(log_dir)),
    }

    # Add cost if available (OpenRouter provides this with "usage": {"include": True})
    if usage and getattr(usage, "cost", None) is not None:
        metadata["cost_usd"] = float(getattr(usage, "cost"))

    # Add cached tokens if available (prompt caching)
    if usage and hasattr(usage, "prompt_tokens_details"):
        details = usage.prompt_tokens_details
        if details and hasattr(details, "cached_tokens") and details.cached_tokens:
            metadata["cached_prompt_tokens"] = details.cached_tokens

    return metadata

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

from omni_x.core import Run, Task, log
from omni_x.utils.task import load


def import_seeds(run: Run, seeds: Iterable[Path]) -> None:
    """Import seed tasks from given directories.

    Each directory should contain either:
    1. description.txt & env.py (simple mode): Creates a task with success=True, auto-archives
    2. task.json (configurable mode): Loads task state from JSON
       - If description.txt/env.py exist and task.description/code are null, loads from files
       - This allows configuring task state (interesting, trained, success) while keeping code/description in separate files
       - If task is archivable, adds to archive; otherwise saves to wip (requires resuming to pick up from state)

    Examples:
    - Successful seed: description.txt + env.py (no task.json)
    - Interesting but not trained: task.json with interesting=true, trained=null + description.txt + env.py
    - Partial seed needing env generation: task.json with description="..." and code=null
    """

    for seed in seeds:
        if (seed / "task.json").is_file():
            task = load(seed)
            log("Importing from task file.", run=run, task=task, seed=seed)

            # load description and code from files if present and not already set
            desc_file = seed / "description.txt"
            code_file = seed / "env.py"
            if desc_file.is_file() and task.description is None:
                task.description = desc_file.read_text(encoding="utf-8")
            if code_file.is_file() and task.code is None:
                task.code = code_file.read_text(encoding="utf-8")

            run.archive.save(task)
            if task.is_archivable:
                run.add_to_archive(task)
            else:
                log(f"Seed not archived. Resume to pick up from state.", run=run, task=task, level=logging.WARNING)
            continue

        log("Importing from description+code", run=run, seed=seed)
        desc_file = seed / "description.txt"
        code_file = seed / "env.py"
        assert desc_file.is_file() and code_file.is_file()

        task = Task(
            id=seed.name,
            parents=[],
            description=desc_file.read_text(encoding="utf-8"),
            code=code_file.read_text(encoding="utf-8"),
            interesting=True,
            trained=True,
            success=True,
            done=False,
        )
        run.add_to_archive(task)
        task.done = True
        run.archive.save(task)


def save_run_config(run: Run) -> None:
    """Append run.config to run.json config list only if changed; create the file with current config if missing.
    This allows tracking the history of config changes over time. The config of the run object is not modified.
    """
    run.dir.mkdir(parents=True, exist_ok=True)
    run_file = run.dir / "run.json"
    if run_file.exists():
        data = json.loads(run_file.read_text(encoding="utf-8"))
    else:
        data = {"id": run.name, "configs": []}

    cfg_now = asdict(run.config)
    configs = data.setdefault("configs", [])
    latest = max(configs, key=lambda c: c.get("created", 0)) if configs else None
    latest_cfg = latest.get("config") if latest else None

    if latest_cfg == cfg_now:
        log("Config unchanged; Skipping save.", run=run)
        return

    configs.append({"created": time.time(), "config": cfg_now})
    run_file.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    log("Saved run config.", run=run)


def load_run_config(dir: Path, config_cls: type[DataclassInstance]) -> DataclassInstance:
    """Load latest config from dir/run.json and return a dataclass instance."""
    data = json.loads((dir / "run.json").read_text(encoding="utf-8"))
    configs = data.get("configs", [])
    assert configs, "No configs found in run.json"
    latest = max(configs, key=lambda c: c.get("created", 0)).get("config")
    return config_cls(**latest)

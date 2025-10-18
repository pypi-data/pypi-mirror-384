import json
import os
import tempfile
from pathlib import Path

from omni_x.core import Task


def save(task: Task, dir: Path, write_artifacts: bool) -> None:
    dir.mkdir(parents=True, exist_ok=True)
    _atomic_write(dir / "task.json", json.dumps(task.to_dict(), indent=2, default=str))

    if write_artifacts:
        if task.code:
            (dir / "env.py").write_text(task.code)
        if task.description:
            (dir / "description.txt").write_text(task.description)


def load(dir: Path) -> Task:
    data = json.loads((dir / "task.json").read_text(encoding="utf-8"))
    return Task.from_dict(data)


def _atomic_write(file: Path, data: str, encoding="utf-8") -> None:
    fd, tmp = tempfile.mkstemp(prefix=".tmp.atomic.", dir=str(file.parent))
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, file)
    except Exception:
        os.remove(tmp)
        raise

from pathlib import Path
from typing import Iterator

from omni_x.core import Archive, Task
from omni_x.utils.task import load, save


class FsArchive(Archive):
    """Filesystem-based Archive implementation."""

    wip_dir = "wip"
    archived_dir = "archived"
    discarded_dir = "discarded"

    def __init__(self, dir: str | Path) -> None:
        self.root = Path(dir)

        self.archived_path = self.root / self.archived_dir
        self.archived_path.mkdir(parents=True, exist_ok=True)

        self.wip_path = self.root / self.wip_dir
        self.wip_path.mkdir(parents=True, exist_ok=True)

        self.discarded_path = self.root / self.discarded_dir
        self.discarded_path.mkdir(parents=True, exist_ok=True)

    def __len__(self) -> int:
        path = self.root / self.archived_dir
        if not path.exists():
            return 0
        return sum(1 for p in path.iterdir() if p.is_dir() and p.name.isdigit())

    def save(self, task: Task) -> Task:
        if task.archive_idx is not None:  # to-archive or already archived
            path = self.archived_path / str(task.archive_idx)

            # moving from wip to archived, if wip exists and archived doesn't
            src = self.wip_path / task.id
            if not path.exists() and src.exists():
                src.rename(path)

        elif task.is_discardable:
            path = self.discarded_path / task.id
        else:
            path = self.wip_path / task.id

        save(task, path, write_artifacts=True)
        return task

    def get(self, id: str | int) -> Task:
        dirs = (
            (self.archived_path,)
            if isinstance(id, int) or id.isdigit()
            else (self.wip_path, self.archived_path, self.discarded_path)
        )

        task_dir = next((d for d in dirs if (d / str(id)).is_dir()), None)
        if task_dir:
            return load(task_dir / str(id))

        raise KeyError(f"Task {id} not found in archive.")

    def get_archived(self) -> Iterator[Task]:
        path = self.root / self.archived_dir
        if not path.exists():
            return iter(())
        return (load(p) for p in sorted(path.iterdir()) if p.is_dir() and p.name.isdigit())

    def get_discarded(self) -> Iterator[Task]:
        path = self.root / self.discarded_dir
        if not path.exists():
            return iter(())
        return (load(p) for p in sorted(path.iterdir()) if p.is_dir())

    def get_wip(self) -> Iterator[Task]:
        path = self.root / self.wip_dir
        if not path.exists():
            return iter(())
        return (load(p) for p in sorted(path.iterdir()) if p.is_dir())

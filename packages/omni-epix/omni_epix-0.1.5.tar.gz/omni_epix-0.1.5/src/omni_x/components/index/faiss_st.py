from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from omni_x.core import Task, TaskIndex, log


class FaissTaskIndex(TaskIndex):
    def __init__(self, dir: Path, model: str, dim: int | None = None) -> None:
        self.embedder = Embedder(model)
        dim = dim or self.embedder.model.get_sentence_embedding_dimension()
        assert dim, "Could not determine embedding dimension, please provide it explicitly"
        self.index = FaissVectorIndex(dir, dim=dim)

    def add(self, task: Task) -> None:
        assert task.archive_idx is not None, "Task must have an archive_idx to be added to the index"

        embedding = self.embedder([task.embedding_text])
        n_added = self.index.add([task.archive_idx], embedding)

        log(f"Added task {task.id} to index" if n_added else f"Task {task.id} already in index", task=task)

    def search(self, query: str, k: int) -> tuple[list[int], list[float]]:
        embedding = self.embedder([query])
        results = self.index.search(embedding, k=k)[0]  # only one query
        tasks = [task_idx for task_idx, _ in results]
        scores = [score for _, score in results]
        return tasks, scores


class Embedder:
    def __init__(self, model_name: str) -> None:
        self.model = SentenceTransformer(model_name)

    def __call__(self, texts: list[str]) -> np.ndarray:
        """Returns (N, D)"""
        embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.astype("float32", copy=False)


class FaissVectorIndex:
    """Cosine-similarity index over task embeddings."""

    def __init__(self, dir: Path, dim: int) -> None:
        self.dirpath = dir
        self.dim = dim

        self.dirpath.mkdir(parents=True, exist_ok=True)
        self.index_path = dir / "index.faiss"
        self.ids_path = dir / "ids.jsonl"
        self._ids: set[int] = set()

        self._load_index()

    def _load_index(self) -> None:
        base = faiss.IndexFlatIP(self.dim)
        self.index = faiss.IndexIDMap2(base)
        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
        if self.ids_path.exists():
            for line in self.ids_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                self._ids.add(int(line))

    def add(self, task_idxs: list[int], embeddings: np.ndarray) -> int:
        """Add new embeddings that MUST have L2 norm of 1.0 (for cosine similarity) to the index.

        Returns the number of new embeddings added (0 if all keys already exist).
        """
        assert embeddings.ndim == 2 and embeddings.shape[1] == self.dim, f"Embeddings must be of shape (N, {self.dim})"
        assert len(task_idxs) == embeddings.shape[0]

        to_add = [(row, int(task_idx)) for row, task_idx in enumerate(task_idxs) if int(task_idx) not in self._ids]
        if not to_add:
            return 0
        rows_to_add, ids_to_add = map(list, zip(*to_add))

        embeddings_to_add = np.ascontiguousarray(embeddings[rows_to_add], dtype=np.float32)
        ids_to_add_np = np.array(ids_to_add, dtype=np.int64)

        self.index.add_with_ids(x=embeddings_to_add, ids=ids_to_add_np)  # type: ignore  # faiss type stubs are wrong...

        with self.ids_path.open("a", encoding="utf-8") as f:
            for id_val in ids_to_add:
                self._ids.add(int(id_val))
                f.write(f"{int(id_val)}\n")
        faiss.write_index(self.index, str(self.index_path))
        return len(ids_to_add)

    def search(self, query_embeddings: np.ndarray, k: int) -> list[list[tuple[int, float]]]:
        """Search the index for the top_k most similar embeddings for each query embedding.

        Returns a list of lists of (archive_idx, similarity score) tuples of shape (Q,topK,2).
        """
        assert k > 0, "k must be greater than 0"

        query_embeddings = query_embeddings.reshape(-1, self.dim).astype(np.float32)

        sims, ids = self.index.search(x=query_embeddings, k=k)  # type: ignore  # faiss type stubs are wrong...
        return [[(int(id64), float(sim)) for id64, sim in zip(id_row, sim_row) if int(id64) != -1] for id_row, sim_row in zip(ids, sims)]

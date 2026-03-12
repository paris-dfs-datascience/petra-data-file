from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import faiss
import numpy as np


@dataclass
class VectorRecord:
    id: str
    image_path: str
    page_number: int  # 1-based
    metadata: dict[str, Any]


class ImageFaissStore:
    def __init__(self, dim: int, metric: str = "cosine"):
        self.dim = dim
        self.metric = metric
        if metric == "cosine":
            # cosine via inner product on normalized vectors
            self.index = faiss.IndexFlatIP(dim)
        else:
            raise ValueError("Only cosine metric is implemented")
        self.ids: list[str] = []
        self.records: list[VectorRecord] = []

    def add(self, embeddings: np.ndarray, records: list[VectorRecord]):
        assert embeddings.shape[0] == len(records)
        # normalize for cosine
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-12
        vecs = embeddings / norms
        self.index.add(vecs.astype("float32"))
        self.ids.extend([r.id for r in records])
        self.records.extend(records)

    def search(self, query: np.ndarray, k: int = 5):
        # normalize
        q = query / (np.linalg.norm(query) + 1e-12)
        D, I = self.index.search(q.reshape(1, -1).astype("float32"), k)
        results = []
        for score, idx in zip(D[0], I[0]):
            if idx == -1:
                continue
            rec = self.records[idx]
            results.append((score, rec))
        return results

    def save(self, index_path: str, meta_path: str):
        faiss.write_index(self.index, index_path)
        meta = {
            "dim": self.dim,
            "metric": self.metric,
            "records": [r.__dict__ for r in self.records],
        }
        Path(meta_path).write_text(json.dumps(meta, indent=2))

    @classmethod
    def load(cls, index_path: str, meta_path: str) -> "ImageFaissStore":
        index = faiss.read_index(index_path)
        meta = json.loads(Path(meta_path).read_text())
        dim = meta["dim"]
        store = cls(dim=dim, metric=meta["metric"])
        store.index = index
        store.records = [VectorRecord(**r) for r in meta["records"]]
        store.ids = [r.id for r in store.records]
        return store

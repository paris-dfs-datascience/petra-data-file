from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np

from src.vectorstore.faiss_store import ImageFaissStore, VectorRecord
from src.providers.base_embeddings import EmbeddingsProvider


def build_index_from_images(
    image_paths: list[str],
    embedder: EmbeddingsProvider,
    doc_id: str,
) -> ImageFaissStore:
    vecs = embedder.embed_images(image_paths)
    records = []
    for i, p in enumerate(image_paths):
        rec = VectorRecord(
            id=f"{doc_id}_p{i+1}",
            image_path=p,
            page_number=i + 1,
            metadata={"doc_id": doc_id},
        )
        records.append(rec)
    store = ImageFaissStore(dim=embedder.dim, metric="cosine")
    store.add(vecs, records)
    return store


def retrieve_pages_for_rule(
    rule_query: str,
    embedder: EmbeddingsProvider,
    store: ImageFaissStore,
    top_k: int = 5,
) -> list[VectorRecord]:
    q = embedder.embed_texts([rule_query])[0]
    hits = store.search(q, k=top_k)
    # Sort by page_number to maintain PDF order
    records = [r for _, r in hits]
    records.sort(key=lambda rec: rec.page_number)
    return records

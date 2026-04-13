"""Semantic retriever for earnings transcript chunks."""
from __future__ import annotations

import logging
from typing import Any

from rag.indexer import COLLECTION_NAME, _get_client, _get_embedder

logger = logging.getLogger(__name__)


def search_passages(
    ticker: str,
    query: str,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Semantic search over indexed transcript chunks, filtered by ticker.

    Returns a list of dicts: {text, quarter, section, score, chunk_index}.
    Higher score = more relevant (we convert Chroma's distance).
    """
    client = _get_client()
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME, embedding_function=_get_embedder()
    )

    result = collection.query(
        query_texts=[query],
        n_results=top_k,
        where={"ticker": ticker.upper()},
    )

    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    dists = result.get("distances", [[]])[0]

    out: list[dict[str, Any]] = []
    for doc, meta, dist in zip(docs, metas, dists):
        out.append({
            "text": doc,
            "quarter": meta.get("quarter"),
            "section": meta.get("section"),
            "chunk_index": meta.get("chunk_index"),
            "score": round(1.0 / (1.0 + float(dist)), 4),
        })
    return out

"""
Transcript indexer — chunks earnings call transcripts by section/paragraph,
embeds with sentence-transformers, stores in a persistent ChromaDB collection.

Each chunk carries metadata: ticker, quarter, section_name, chunk_index.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Iterable

import config

logger = logging.getLogger(__name__)

CHROMA_DIR: Path = config.MOCK_DATA_DIR / "chroma_db"
COLLECTION_NAME = "earnings_transcripts"
EMBED_MODEL = "all-MiniLM-L6-v2"

# Rough word-count window per chunk
MIN_CHUNK_WORDS = 120
MAX_CHUNK_WORDS = 450

# Section header patterns we expect from the generator
_SECTION_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("Opening Remarks", re.compile(r"^Operator:\s*Good", re.IGNORECASE)),
    ("CEO Strategic Update", re.compile(r",\s*CEO:\s*Thank you", re.IGNORECASE)),
    ("CFO Financial Review", re.compile(r",\s*CFO:\s*Thank you", re.IGNORECASE)),
    ("Segment Breakdown", re.compile(r"additional segment color", re.IGNORECASE)),
    ("Q&A", re.compile(r"question-and-answer session", re.IGNORECASE)),
]


def _split_sections(text: str) -> list[tuple[str, str]]:
    """Split transcript text into (section_name, section_text) tuples."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    sections: list[tuple[str, list[str]]] = []
    current_name = "Opening Remarks"
    current_paras: list[str] = []
    for para in paragraphs:
        matched = None
        for name, pattern in _SECTION_PATTERNS:
            if pattern.search(para):
                matched = name
                break
        if matched and matched != current_name and current_paras:
            sections.append((current_name, current_paras))
            current_name = matched
            current_paras = [para]
        else:
            if matched:
                current_name = matched
            current_paras.append(para)
    if current_paras:
        sections.append((current_name, current_paras))
    return [(name, "\n\n".join(paras)) for name, paras in sections]


def _chunk_section(section_text: str) -> list[str]:
    """Split section into paragraph-grouped chunks of roughly 120-450 words."""
    paragraphs = [p for p in section_text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf: list[str] = []
    buf_wc = 0
    for para in paragraphs:
        wc = len(para.split())
        if buf and buf_wc + wc > MAX_CHUNK_WORDS:
            chunks.append("\n\n".join(buf))
            buf = [para]
            buf_wc = wc
        else:
            buf.append(para)
            buf_wc += wc
        if buf_wc >= MIN_CHUNK_WORDS and buf_wc >= MAX_CHUNK_WORDS * 0.6:
            # emit on natural break
            chunks.append("\n\n".join(buf))
            buf = []
            buf_wc = 0
    if buf:
        if chunks and buf_wc < MIN_CHUNK_WORDS:
            chunks[-1] = chunks[-1] + "\n\n" + "\n\n".join(buf)
        else:
            chunks.append("\n\n".join(buf))
    return chunks


def _iter_chunks(ticker: str, quarters: list[dict]) -> Iterable[dict]:
    for q in quarters:
        quarter = q.get("quarter", "unknown")
        text = q.get("text", "")
        if not text:
            continue
        for section_name, section_text in _split_sections(text):
            for i, chunk in enumerate(_chunk_section(section_text)):
                yield {
                    "id": f"{ticker}_{quarter}_{section_name.replace(' ', '_')}_{i}",
                    "text": chunk,
                    "metadata": {
                        "ticker": ticker,
                        "quarter": quarter,
                        "section": section_name,
                        "chunk_index": i,
                    },
                }


def _get_client():
    import chromadb
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def _get_embedder():
    from chromadb.utils import embedding_functions
    return embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)


def index_exists() -> bool:
    """Return True if a persistent Chroma collection is already populated."""
    if not CHROMA_DIR.exists():
        return False
    try:
        client = _get_client()
        col = client.get_or_create_collection(
            name=COLLECTION_NAME, embedding_function=_get_embedder()
        )
        return col.count() > 0
    except Exception as e:
        logger.warning(f"Could not check index: {e}")
        return False


def build_index(tickers: list[str] | None = None, rebuild: bool = False) -> int:
    """
    Build the vector index over all (ticker, quarter) transcripts.

    Returns number of chunks indexed.
    """
    from data import mock_client

    if tickers is None:
        tickers = ["AAPL", "JPM", "JNJ", "XOM", "WMT"]

    client = _get_client()
    embedder = _get_embedder()

    if rebuild:
        try:
            client.delete_collection(COLLECTION_NAME)
            logger.info(f"Dropped existing collection: {COLLECTION_NAME}")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME, embedding_function=embedder
    )

    ids: list[str] = []
    docs: list[str] = []
    metas: list[dict] = []

    for ticker in tickers:
        quarters = mock_client.query_all_transcripts(ticker)
        for chunk in _iter_chunks(ticker, quarters):
            ids.append(chunk["id"])
            docs.append(chunk["text"])
            metas.append(chunk["metadata"])

    if not ids:
        logger.warning("No chunks produced — nothing to index.")
        return 0

    # Upsert in batches (Chroma has batch size limits)
    BATCH = 100
    for i in range(0, len(ids), BATCH):
        collection.upsert(
            ids=ids[i:i + BATCH],
            documents=docs[i:i + BATCH],
            metadatas=metas[i:i + BATCH],
        )

    logger.info(f"Indexed {len(ids)} chunks across {len(tickers)} tickers.")
    return len(ids)

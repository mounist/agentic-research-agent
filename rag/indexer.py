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

CHROMA_DIR: Path = config.CACHE_DIR / "chroma_db"
COLLECTION_NAME = "earnings_transcripts"
EMBED_MODEL = "all-MiniLM-L6-v2"

# Rough word-count window per chunk
MIN_CHUNK_WORDS = 120
MAX_CHUNK_WORDS = 450

# Mock-generator section-header patterns (explicit labeled sections).
_MOCK_SECTION_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("Opening Remarks", re.compile(r"^Operator:\s*Good", re.IGNORECASE)),
    ("CEO Strategic Update", re.compile(r",\s*CEO:\s*Thank you", re.IGNORECASE)),
    ("CFO Financial Review", re.compile(r",\s*CFO:\s*Thank you", re.IGNORECASE)),
    ("Segment Breakdown", re.compile(r"additional segment color", re.IGNORECASE)),
    ("Q&A", re.compile(r"question-and-answer session", re.IGNORECASE)),
]

# Live-WRDS section-header patterns. Real CIQ transcripts lack explicit
# labeled sections — they are speaker-turn streams ("Operator", "<Name> -
# <Title>", "Analyst - <Name>"). We bucket speaker-turn types into coarse
# sections; anything unrecognised stays in the current section.
_LIVE_SECTION_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("Q&A", re.compile(r"question[-\s]and[-\s]answer", re.IGNORECASE)),
    ("Q&A", re.compile(r"^Analyst\s*[-–]", re.IGNORECASE | re.MULTILINE)),
    ("Prepared Remarks", re.compile(r"^Executive\s*[-–]", re.IGNORECASE | re.MULTILINE)),
    ("Prepared Remarks", re.compile(r"\b(CEO|CFO|Chief Executive|Chief Financial)\b", re.IGNORECASE)),
    ("Opening Remarks", re.compile(r"^Operator\b", re.IGNORECASE | re.MULTILINE)),
]


def _split_sections(text: str, data_mode: str = "mock") -> list[tuple[str, str]]:
    """Split transcript text into (section_name, section_text) tuples.

    For ``data_mode="live"`` we try live-WRDS speaker patterns first, then
    fall back to a single ``Transcript`` section of generic paragraphs if
    no live markers are found. For ``data_mode="mock"`` we use the
    explicit labeled-section patterns written by the mock generator.
    """
    if data_mode == "live":
        primary = _LIVE_SECTION_PATTERNS
        default_name = "Transcript"
    else:
        primary = _MOCK_SECTION_PATTERNS
        default_name = "Opening Remarks"

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    sections: list[tuple[str, list[str]]] = []
    current_name = default_name
    current_paras: list[str] = []
    any_match = False
    for para in paragraphs:
        matched = None
        for name, pattern in primary:
            if pattern.search(para):
                matched = name
                break
        if matched:
            any_match = True
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

    # Live fallback: if no live markers were found, emit one generic
    # section so the paragraph-level chunker handles the whole doc.
    if data_mode == "live" and not any_match:
        return [("Transcript", text)]

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


def _iter_chunks(ticker: str, quarters: list[dict], data_mode: str = "mock") -> Iterable[dict]:
    for q in quarters:
        quarter = q.get("quarter", "unknown")
        tid = q.get("transcriptid")
        text = q.get("text", "") or q.get("componenttext", "")
        if not text:
            continue
        uid = str(tid) if tid is not None else quarter
        global_i = 0
        for section_name, section_text in _split_sections(text, data_mode=data_mode):
            for i, chunk in enumerate(_chunk_section(section_text)):
                yield {
                    "id": f"{ticker}_{quarter}_{uid}_{section_name.replace(' ', '_')}_{i}_{global_i}",
                    "text": chunk,
                    "metadata": {
                        "ticker": ticker,
                        "quarter": quarter,
                        "section": section_name,
                        "chunk_index": i,
                    },
                }
                global_i += 1


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


def build_index(
    tickers: list[str] | None = None,
    rebuild: bool = False,
    data_mode: str = "live",
) -> int:
    """
    Build the vector index over all (ticker, quarter) transcripts.

    Parameters
    ----------
    tickers : list of ticker strings to index (defaults to the eval universe).
    rebuild : drop the existing collection before indexing.
    data_mode : ``"live"`` pulls from WRDS, ``"mock"`` from bundled fixtures.

    Returns number of chunks indexed.
    """
    if data_mode == "live":
        from data import wrds_client as _client
    else:
        from data import mock_client as _client

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
        if not hasattr(_client, "query_all_transcripts"):
            logger.warning(
                f"{data_mode} client has no query_all_transcripts; skipping {ticker}"
            )
            continue
        quarters = _client.query_all_transcripts(ticker)
        for chunk in _iter_chunks(ticker, quarters, data_mode=data_mode):
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

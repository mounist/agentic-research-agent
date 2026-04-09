"""JSON-backed persistent memory store at ~/.finagent/research_memory.json."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import config

logger = logging.getLogger(__name__)


def _load_store() -> dict[str, Any]:
    """Read the full store from disk."""
    if config.MEMORY_PATH.exists():
        try:
            return json.loads(config.MEMORY_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("Corrupt memory file — starting fresh.")
    return {"research": {}, "metadata": {"total_researches": 0, "last_run": None}}


def _write_store(store: dict[str, Any]) -> None:
    """Write the full store to disk."""
    config.MEMORY_PATH.write_text(
        json.dumps(store, indent=2, default=str), encoding="utf-8"
    )


def save_research(entry: dict[str, Any]) -> None:
    """Upsert a research entry keyed by ticker."""
    store = _load_store()
    ticker = entry["ticker"].upper()
    entry["last_updated"] = datetime.now(timezone.utc).isoformat()
    store["research"][ticker] = entry
    store["metadata"]["total_researches"] = len(store["research"])
    store["metadata"]["last_run"] = entry["last_updated"]
    _write_store(store)
    logger.info(f"Saved research for {ticker} to memory.")


def query_by_ticker(ticker: str) -> dict[str, Any] | None:
    """Look up prior research for a specific ticker."""
    store = _load_store()
    return store["research"].get(ticker.upper())


def query_by_sector(sector: str, n: int = 5) -> list[dict[str, Any]]:
    """Find research entries matching a sector (case-insensitive substring)."""
    store = _load_store()
    sector_lower = sector.lower()
    matches = [
        entry for entry in store["research"].values()
        if sector_lower in entry.get("sector", "").lower()
    ]
    # Sort by last_updated descending
    matches.sort(key=lambda e: e.get("last_updated", ""), reverse=True)
    return matches[:n]


def list_all() -> list[dict[str, Any]]:
    """Return all stored research summaries."""
    store = _load_store()
    return list(store["research"].values())


def clear() -> None:
    """Clear all memory (for testing)."""
    _write_store({"research": {}, "metadata": {"total_researches": 0, "last_run": None}})

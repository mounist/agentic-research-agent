"""
Mock data client — returns bundled sample data for demo mode.

Same method signatures as wrds_client. Loads JSON fixtures from mock_data/.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import pandas as pd

import config

logger = logging.getLogger(__name__)

_cache: dict[str, Any] = {}


def _load_fixture(name: str) -> dict[str, Any]:
    """Load a JSON fixture file."""
    if name not in _cache:
        path = config.MOCK_DATA_DIR / f"{name}.json"
        if not path.exists():
            logger.warning(f"Mock fixture not found: {path}")
            return {}
        _cache[name] = json.loads(path.read_text(encoding="utf-8"))
    return _cache[name]


def query_crsp_daily(
    ticker: str,
    start_date: str = config.DEFAULT_START_DATE,
    end_date: str = config.DEFAULT_END_DATE,
) -> pd.DataFrame:
    data = _load_fixture("price_data")
    ticker_data = data.get(ticker.upper(), [])
    if not ticker_data:
        return pd.DataFrame()
    df = pd.DataFrame(ticker_data)
    df["date"] = pd.to_datetime(df["date"])
    mask = (df["date"] >= start_date) & (df["date"] <= end_date)
    return df.loc[mask].reset_index(drop=True)


def query_compustat_fundq(ticker: str, n_quarters: int = 8) -> pd.DataFrame:
    data = _load_fixture("fundamentals")
    ticker_data = data.get(ticker.upper(), [])
    if not ticker_data:
        return pd.DataFrame()
    df = pd.DataFrame(ticker_data[:n_quarters])
    df["datadate"] = pd.to_datetime(df["datadate"])
    return df


def query_compustat_company(ticker: str) -> pd.DataFrame:
    data = _load_fixture("company_info")
    info = data.get(ticker.upper())
    if not info:
        return pd.DataFrame()
    return pd.DataFrame([info])


def query_sector_peers(sic2: str, exclude_gvkey: str, n: int = 5) -> pd.DataFrame:
    data = _load_fixture("sector_peers")
    peers = data.get(sic2, [])
    peers = [p for p in peers if p.get("gvkey") != exclude_gvkey]
    return pd.DataFrame(peers[:n]) if peers else pd.DataFrame()


def query_ibes_actuals(ticker: str, n_quarters: int = 8) -> pd.DataFrame:
    data = _load_fixture("earnings_data")
    ticker_data = data.get(ticker.upper(), {}).get("actuals", [])
    if not ticker_data:
        return pd.DataFrame()
    df = pd.DataFrame(ticker_data[:n_quarters])
    for col in ("pends", "anndats"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    return df


def query_ibes_estimates(ticker: str, n_quarters: int = 8) -> pd.DataFrame:
    data = _load_fixture("earnings_data")
    ticker_data = data.get(ticker.upper(), {}).get("estimates", [])
    if not ticker_data:
        return pd.DataFrame()
    df = pd.DataFrame(ticker_data[:n_quarters])
    for col in ("fpedats", "statpers"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    return df


def query_ciq_transcript(ticker: str, quarter: str | None = None) -> pd.DataFrame:
    data = _load_fixture("transcripts")
    ticker_data = data.get(ticker.upper())
    if not ticker_data:
        return pd.DataFrame()

    # Legacy single-dict format (backwards compat)
    if isinstance(ticker_data, dict):
        return pd.DataFrame([ticker_data])

    # New multi-quarter list format
    if quarter:
        match = [q for q in ticker_data if q.get("quarter") == quarter]
        if not match:
            return pd.DataFrame()
        row = dict(match[0])
    else:
        # Most recent = last in list (generator writes chronologically)
        row = dict(sorted(ticker_data, key=lambda q: q.get("transcriptdate", ""))[-1])

    row.setdefault("fiscal_quarter", row.get("quarter", "unknown"))
    return pd.DataFrame([row])


def query_all_transcripts(ticker: str) -> list[dict[str, Any]]:
    """Return all quarters of transcripts for `ticker` (used for RAG indexing)."""
    data = _load_fixture("transcripts")
    ticker_data = data.get(ticker.upper())
    if not ticker_data:
        return []
    if isinstance(ticker_data, dict):
        return [ticker_data]
    return list(ticker_data)


def resolve_ticker_to_permno(ticker: str) -> int | None:
    mapping = {"AAPL": 14593, "JPM": 47896, "JNJ": 22111, "XOM": 11850, "WMT": 55976}
    return mapping.get(ticker.upper())


def resolve_ticker_to_gvkey(ticker: str) -> str | None:
    mapping = {"AAPL": "001690", "JPM": "004297", "JNJ": "004010", "XOM": "003255", "WMT": "011259"}
    return mapping.get(ticker.upper())


def close() -> None:
    """No-op for mock."""
    pass

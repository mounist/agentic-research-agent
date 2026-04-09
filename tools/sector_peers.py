"""Tool: get_sector_peers — find same-sector companies and compare."""
from __future__ import annotations

from typing import Any

from agent.models import ToolResult
import config


def _get_client(data_mode: str):
    if data_mode == "live":
        from data import wrds_client as client
    else:
        from data import mock_client as client
    return client


def get_sector_peers(
    ticker: str,
    n_peers: int = 5,
    data_mode: str = "mock",
    **kwargs: Any,
) -> ToolResult:
    """Find same-sector peers with key comparison metrics."""
    client = _get_client(data_mode)

    # Get the reference company's SIC code
    company = client.query_compustat_company(ticker)
    if company.empty:
        return ToolResult(
            tool_name="get_sector_peers",
            success=False,
            error_message=f"No company info found for {ticker}.",
        )

    row = company.iloc[0]
    sic = str(row.get("sic", ""))
    sic2 = sic[:2] if len(sic) >= 2 else ""
    gvkey = str(row.get("gvkey", ""))
    company_name = str(row.get("conm", ticker))

    if not sic2:
        return ToolResult(
            tool_name="get_sector_peers",
            success=False,
            error_message=f"No SIC code found for {ticker}.",
        )

    # Get peers
    peers_df = client.query_sector_peers(sic2, gvkey, n_peers)
    peers = []
    if not peers_df.empty:
        for _, p in peers_df.iterrows():
            rev = _safe_float(p.get("revtq"))
            ni = _safe_float(p.get("niq"))
            eps = _safe_float(p.get("epspxq"))
            price = _safe_float(p.get("prccq"))
            shares = _safe_float(p.get("cshoq"))
            mcap = (price * shares) if (price and shares) else None

            peers.append({
                "ticker": str(p.get("tic", "")),
                "name": str(p.get("conm", "")),
                "market_cap_m": round(mcap, 1) if mcap else None,
                "revenue_m": round(rev, 1) if rev else None,
                "net_income_m": round(ni, 1) if ni else None,
                "eps": round(eps, 2) if eps else None,
            })

    return ToolResult(
        tool_name="get_sector_peers",
        success=True,
        data={
            "ticker": ticker.upper(),
            "company_name": company_name,
            "sic_code": sic,
            "sic_2digit": sic2,
            "n_peers_found": len(peers),
            "peers": peers,
        },
    )


def _safe_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        import math
        f = float(val)
        return None if math.isnan(f) else f
    except (ValueError, TypeError):
        return None

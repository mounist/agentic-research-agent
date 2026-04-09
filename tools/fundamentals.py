"""Tool: get_fundamentals — Compustat quarterly fundamentals."""
from __future__ import annotations

from typing import Any

import pandas as pd

from agent.models import ToolResult
import config


def _get_client(data_mode: str):
    if data_mode == "live":
        from data import wrds_client as client
    else:
        from data import mock_client as client
    return client


def get_fundamentals(
    ticker: str,
    n_quarters: int = 8,
    data_mode: str = "mock",
    **kwargs: Any,
) -> ToolResult:
    """Pull quarterly fundamentals for a ticker."""
    client = _get_client(data_mode)
    df = client.query_compustat_fundq(ticker, n_quarters)
    if df.empty:
        return ToolResult(
            tool_name="get_fundamentals",
            success=False,
            error_message=f"No Compustat data found for {ticker}.",
        )

    quarters = []
    for _, row in df.iterrows():
        rev = _safe_float(row.get("revtq"))
        if rev is None:
            rev = _safe_float(row.get("saleq"))
        ni = _safe_float(row.get("niq"))
        eps_basic = _safe_float(row.get("epspxq"))
        eps_diluted = _safe_float(row.get("epsfxq"))
        assets = _safe_float(row.get("atq"))
        liab = _safe_float(row.get("ltq"))
        equity = _safe_float(row.get("ceqq"))
        op_income = _safe_float(row.get("oiadpq"))
        gp = _safe_float(row.get("gpq"))
        price = _safe_float(row.get("prccq"))
        shares = _safe_float(row.get("cshoq"))

        gross_margin = (gp / rev) if (rev and gp) else None
        op_margin = (op_income / rev) if (rev and op_income) else None
        net_margin = (ni / rev) if (rev and ni) else None
        roe = (ni / equity) if (equity and ni) else None
        roa = (ni / assets) if (assets and ni) else None
        de_ratio = (liab / equity) if (equity and liab) else None
        mcap = (price * shares) if (price and shares) else None

        quarters.append({
            "period": f"{int(row.get('fyearq', 0))}Q{int(row.get('fqtr', 0))}",
            "datadate": str(row["datadate"].date()) if hasattr(row["datadate"], "date") else str(row["datadate"]),
            "revenue_m": round(rev, 1) if rev else None,
            "net_income_m": round(ni, 1) if ni else None,
            "eps_basic": round(eps_basic, 2) if eps_basic else None,
            "eps_diluted": round(eps_diluted, 2) if eps_diluted else None,
            "gross_margin": round(gross_margin, 4) if gross_margin else None,
            "operating_margin": round(op_margin, 4) if op_margin else None,
            "net_margin": round(net_margin, 4) if net_margin else None,
            "roe": round(roe, 4) if roe else None,
            "roa": round(roa, 4) if roa else None,
            "debt_to_equity": round(de_ratio, 2) if de_ratio else None,
            "market_cap_m": round(mcap, 1) if mcap else None,
        })

    return ToolResult(
        tool_name="get_fundamentals",
        success=True,
        data={
            "ticker": ticker.upper(),
            "n_quarters": len(quarters),
            "quarters": quarters,
        },
    )


def _safe_float(val: Any) -> float | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

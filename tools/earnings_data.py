"""Tool: get_earnings_data — IBES actuals vs consensus estimates."""
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


def get_earnings_data(
    ticker: str,
    n_quarters: int = 8,
    data_mode: str = "mock",
    **kwargs: Any,
) -> ToolResult:
    """Pull EPS actuals vs analyst estimates."""
    client = _get_client(data_mode)
    actuals = client.query_ibes_actuals(ticker, n_quarters)
    estimates = client.query_ibes_estimates(ticker, n_quarters)

    if actuals.empty and estimates.empty:
        return ToolResult(
            tool_name="get_earnings_data",
            success=False,
            error_message=f"No IBES data found for {ticker}.",
        )

    quarters = []

    if not estimates.empty:
        for _, row in estimates.iterrows():
            actual = _safe_float(row.get("actual"))
            mean_est = _safe_float(row.get("meanest"))
            med_est = _safe_float(row.get("medest"))
            std_est = _safe_float(row.get("stdev"))
            n_analysts = _safe_int(row.get("numest"))

            surprise = (actual - mean_est) if (actual is not None and mean_est is not None) else None
            surprise_pct = (surprise / abs(mean_est)) if (surprise is not None and mean_est and mean_est != 0) else None
            sue = (surprise / std_est) if (surprise is not None and std_est and std_est > 0) else None

            fpedats = row.get("fpedats")
            statpers = row.get("statpers")

            quarters.append({
                "fiscal_period_end": str(fpedats.date()) if hasattr(fpedats, "date") else str(fpedats),
                "estimate_date": str(statpers.date()) if hasattr(statpers, "date") else str(statpers),
                "actual_eps": round(actual, 3) if actual is not None else None,
                "consensus_mean": round(mean_est, 3) if mean_est is not None else None,
                "consensus_median": round(med_est, 3) if med_est is not None else None,
                "estimate_stdev": round(std_est, 3) if std_est is not None else None,
                "num_analysts": n_analysts,
                "surprise": round(surprise, 3) if surprise is not None else None,
                "surprise_pct": round(surprise_pct, 4) if surprise_pct is not None else None,
                "sue": round(sue, 3) if sue is not None else None,
            })

    elif not actuals.empty:
        for _, row in actuals.iterrows():
            quarters.append({
                "fiscal_period_end": str(row["pends"].date()) if hasattr(row["pends"], "date") else str(row["pends"]),
                "announcement_date": str(row["anndats"].date()) if hasattr(row["anndats"], "date") else str(row["anndats"]),
                "actual_eps": round(float(row["actual_eps"]), 3),
            })

    return ToolResult(
        tool_name="get_earnings_data",
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


def _safe_int(val: Any) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None

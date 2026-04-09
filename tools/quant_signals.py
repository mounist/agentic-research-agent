"""Tool: calculate_quant_signals — compute momentum, SUE, profitability."""
from __future__ import annotations

import json
import math
from typing import Any

from agent.models import ToolResult


def _ensure_dict(val: Any) -> dict[str, Any] | None:
    """Convert JSON strings to dicts if needed."""
    if val is None:
        return None
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return None
    if isinstance(val, dict):
        return val
    return None


def calculate_quant_signals(
    ticker: str,
    price_data: dict[str, Any] | str | None = None,
    fundamentals: dict[str, Any] | str | None = None,
    earnings_data: dict[str, Any] | str | None = None,
    data_mode: str = "mock",
    **kwargs: Any,
) -> ToolResult:
    price_data = _ensure_dict(price_data)
    fundamentals = _ensure_dict(fundamentals)
    earnings_data = _ensure_dict(earnings_data)
    """Compute quantitative signals from previously gathered data."""
    signals: dict[str, Any] = {"ticker": ticker.upper()}

    # ── Momentum & volatility from price data ───────────────────────
    if price_data and "daily_returns_last_252" in price_data:
        rets = price_data["daily_returns_last_252"]
        if rets:
            signals["momentum_1m"] = _cum_return(rets[-21:])
            signals["momentum_3m"] = _cum_return(rets[-63:])
            signals["momentum_6m"] = _cum_return(rets[-126:])
            signals["momentum_12m"] = _cum_return(rets[-252:])
            signals["volatility_20d"] = _annualised_vol(rets[-20:])
            signals["volatility_60d"] = _annualised_vol(rets[-60:])
            signals["latest_price"] = price_data.get("latest_price")
            signals["cumulative_return"] = price_data.get("cumulative_return")

    # ── Earnings signals ────────────────────────────────────────────
    if earnings_data and "quarters" in earnings_data:
        quarters = earnings_data["quarters"]
        if quarters:
            latest = quarters[0]
            signals["sue_latest"] = latest.get("sue")
            signals["latest_surprise_pct"] = latest.get("surprise_pct")
            signals["num_analysts"] = latest.get("num_analysts")

            # Earnings momentum: change in SUE over last 2 quarters
            if len(quarters) >= 2:
                sue0 = quarters[0].get("sue")
                sue1 = quarters[1].get("sue")
                if sue0 is not None and sue1 is not None:
                    signals["earnings_momentum"] = round(sue0 - sue1, 3)

            # Revision signal: trend in consensus mean
            means = [q.get("consensus_mean") for q in quarters if q.get("consensus_mean") is not None]
            if len(means) >= 2:
                signals["revision_signal"] = round(means[0] - means[-1], 3)

    # ── Profitability from fundamentals ─────────────────────────────
    if fundamentals and "quarters" in fundamentals:
        quarters = fundamentals["quarters"]
        if quarters:
            latest = quarters[0]
            gm = latest.get("gross_margin")
            om = latest.get("operating_margin")
            nm = latest.get("net_margin")
            roe = latest.get("roe")

            # Simple composite profitability score (average of available margins + ROE)
            prof_components = [x for x in [gm, om, nm, roe] if x is not None]
            if prof_components:
                signals["profitability_score"] = round(sum(prof_components) / len(prof_components), 4)

            signals["gross_margin"] = gm
            signals["operating_margin"] = om
            signals["net_margin"] = nm
            signals["roe"] = roe
            signals["debt_to_equity"] = latest.get("debt_to_equity")

            # Revenue growth (QoQ if available)
            if len(quarters) >= 2:
                rev0 = quarters[0].get("revenue_m")
                rev1 = quarters[1].get("revenue_m")
                if rev0 and rev1 and rev1 != 0:
                    signals["revenue_growth_qoq"] = round((rev0 - rev1) / abs(rev1), 4)

    # Clean out None values
    signals = {k: v for k, v in signals.items() if v is not None}

    return ToolResult(
        tool_name="calculate_quant_signals",
        success=True,
        data=signals,
    )


def _cum_return(rets: list[float]) -> float | None:
    if not rets:
        return None
    prod = 1.0
    for r in rets:
        prod *= (1 + r)
    return round(prod - 1, 4)


def _annualised_vol(rets: list[float]) -> float | None:
    if len(rets) < 2:
        return None
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return round(math.sqrt(var) * math.sqrt(252), 4)

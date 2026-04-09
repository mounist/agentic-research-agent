"""Tool: get_price_data — CRSP daily prices and returns."""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from agent.models import ToolResult
import config


def _get_client(data_mode: str):
    if data_mode == "live":
        from data import wrds_client as client
    else:
        from data import mock_client as client
    return client


def get_price_data(
    ticker: str,
    start_date: str | None = None,
    end_date: str | None = None,
    data_mode: str = "mock",
    **kwargs: Any,
) -> ToolResult:
    """Pull price/return history for a ticker."""
    client = _get_client(data_mode)
    start = start_date or config.DEFAULT_START_DATE
    end = end_date or config.DEFAULT_END_DATE

    df = client.query_crsp_daily(ticker, start, end)
    if df.empty:
        return ToolResult(
            tool_name="get_price_data",
            success=False,
            error_message=f"No CRSP data found for {ticker}.",
        )

    # Clean price (CRSP stores negative prices for bid/ask avg)
    df["prc"] = df["prc"].abs()
    df["ret"] = pd.to_numeric(df["ret"], errors="coerce")

    latest_price = float(df["prc"].iloc[-1])
    cum_return = float((1 + df["ret"].dropna()).prod() - 1)
    ann_vol = float(df["ret"].dropna().std() * math.sqrt(252))
    high_52w = float(df["prc"].tail(252).max()) if len(df) >= 252 else float(df["prc"].max())
    low_52w = float(df["prc"].tail(252).min()) if len(df) >= 252 else float(df["prc"].min())

    # Recent returns for signal computation (last 252 days)
    recent = df.tail(252)
    daily_returns = recent["ret"].dropna().tolist()

    return ToolResult(
        tool_name="get_price_data",
        success=True,
        data={
            "ticker": ticker.upper(),
            "start_date": str(df["date"].iloc[0].date()) if hasattr(df["date"].iloc[0], "date") else str(df["date"].iloc[0]),
            "end_date": str(df["date"].iloc[-1].date()) if hasattr(df["date"].iloc[-1], "date") else str(df["date"].iloc[-1]),
            "n_trading_days": len(df),
            "latest_price": round(latest_price, 2),
            "cumulative_return": round(cum_return, 4),
            "annualised_volatility": round(ann_vol, 4),
            "high_52w": round(high_52w, 2),
            "low_52w": round(low_52w, 2),
            "daily_returns_last_252": [round(r, 6) for r in daily_returns[-252:]],
        },
    )

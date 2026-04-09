"""Tool: get_earnings_transcript — CIQ earnings call transcripts."""
from __future__ import annotations

from typing import Any

from agent.models import ToolResult


def _get_client(data_mode: str):
    if data_mode == "live":
        from data import wrds_client as client
    else:
        from data import mock_client as client
    return client


def get_earnings_transcript(
    ticker: str,
    quarter: str | None = None,
    data_mode: str = "mock",
    **kwargs: Any,
) -> ToolResult:
    """Pull the most recent earnings call transcript."""
    client = _get_client(data_mode)
    df = client.query_ciq_transcript(ticker, quarter)

    if df.empty:
        return ToolResult(
            tool_name="get_earnings_transcript",
            success=False,
            error_message=f"No transcript found for {ticker}.",
        )

    # For live data: concatenate componenttext rows
    if "componenttext" in df.columns and len(df) > 1:
        text = "\n\n".join(df["componenttext"].dropna().astype(str).tolist())
        transcript_date = str(df["transcriptdate"].iloc[0]) if "transcriptdate" in df.columns else "unknown"
        fiscal_q = f"{df['fiscalyear'].iloc[0]}Q{df['fiscalquarter'].iloc[0]}" if "fiscalyear" in df.columns else "unknown"
    else:
        # Mock data: single row with pre-built fields
        row = df.iloc[0]
        text = str(row.get("text", row.get("componenttext", "")))
        transcript_date = str(row.get("transcriptdate", "unknown"))
        fiscal_q = str(row.get("fiscal_quarter", "unknown"))

    # Truncate very long transcripts for context window management
    max_chars = 15000
    truncated = len(text) > max_chars
    if truncated:
        text = text[:max_chars] + "\n\n[... transcript truncated ...]"

    word_count = len(text.split())

    return ToolResult(
        tool_name="get_earnings_transcript",
        success=True,
        data={
            "ticker": ticker.upper(),
            "transcript_date": transcript_date,
            "fiscal_quarter": fiscal_q,
            "word_count": word_count,
            "truncated": truncated,
            "text": text,
        },
    )

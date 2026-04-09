"""Tool: save_research_memory — store completed research to persistent memory."""
from __future__ import annotations

from typing import Any

from agent.models import ToolResult
from memory import store


def save_research_memory(
    ticker: str,
    sector: str,
    recommendation: str,
    confidence: float,
    key_findings: list[str],
    report_summary: str,
    signals: dict[str, Any] | None = None,
    data_mode: str = "mock",
    **kwargs: Any,
) -> ToolResult:
    """Save research findings to persistent memory."""
    entry = {
        "ticker": ticker.upper(),
        "sector": sector,
        "recommendation": recommendation,
        "confidence": confidence,
        "key_findings": key_findings,
        "signals": signals or {},
        "report_summary": report_summary,
    }

    try:
        store.save_research(entry)
        return ToolResult(
            tool_name="save_research_memory",
            success=True,
            data={"message": f"Research for {ticker.upper()} saved to memory."},
        )
    except Exception as e:
        return ToolResult(
            tool_name="save_research_memory",
            success=False,
            error_message=f"Failed to save: {e}",
        )

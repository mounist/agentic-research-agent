"""Tool: query_research_memory — check persistent memory for prior research."""
from __future__ import annotations

from typing import Any

from agent.models import ToolResult
from memory import store


def query_research_memory(
    ticker: str | None = None,
    sector: str | None = None,
    n_results: int = 5,
    data_mode: str = "mock",
    **kwargs: Any,
) -> ToolResult:
    """Check memory for prior research on a ticker or sector."""
    results = []

    if ticker:
        entry = store.query_by_ticker(ticker)
        if entry:
            results.append(entry)

    if sector:
        sector_results = store.query_by_sector(sector, n_results)
        # Avoid duplicates
        seen = {r["ticker"] for r in results}
        for r in sector_results:
            if r["ticker"] not in seen:
                results.append(r)
                seen.add(r["ticker"])

    if not ticker and not sector:
        results = store.list_all()[:n_results]

    return ToolResult(
        tool_name="query_research_memory",
        success=True,
        data={
            "n_results": len(results),
            "prior_research": results[:n_results],
        },
    )

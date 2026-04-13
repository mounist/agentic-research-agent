"""Tool registry — maps tool names to implementations and dispatches calls."""
from __future__ import annotations

import logging
import traceback
from typing import Any, Callable

from agent.models import ToolResult

logger = logging.getLogger(__name__)

# Populated at module load time
TOOL_REGISTRY: dict[str, Callable[..., ToolResult]] = {}


def _register() -> None:
    """Import all tool modules and populate the registry."""
    from tools.price_data import get_price_data
    from tools.fundamentals import get_fundamentals
    from tools.earnings_data import get_earnings_data
    from tools.sector_peers import get_sector_peers
    from tools.earnings_transcript import get_earnings_transcript
    from tools.search_transcript_passages import search_transcript_passages
    from tools.sentiment import analyze_text_sentiment
    from tools.quant_signals import calculate_quant_signals
    from tools.memory_query import query_research_memory
    from tools.memory_save import save_research_memory

    TOOL_REGISTRY.update({
        "get_price_data": get_price_data,
        "get_fundamentals": get_fundamentals,
        "get_earnings_data": get_earnings_data,
        "get_sector_peers": get_sector_peers,
        "get_earnings_transcript": get_earnings_transcript,
        "search_transcript_passages": search_transcript_passages,
        "analyze_text_sentiment": analyze_text_sentiment,
        "calculate_quant_signals": calculate_quant_signals,
        "query_research_memory": query_research_memory,
        "save_research_memory": save_research_memory,
    })


_register()


def dispatch(tool_name: str, params: dict[str, Any], data_mode: str = "mock") -> ToolResult:
    """Look up a tool and call it. Returns error ToolResult if unknown."""
    func = TOOL_REGISTRY.get(tool_name)
    if func is None:
        return ToolResult(
            tool_name=tool_name,
            success=False,
            error_message=f"Unknown tool: {tool_name}",
        )
    try:
        return func(data_mode=data_mode, **params)
    except Exception as e:
        logger.error(f"Tool {tool_name} failed: {e}\n{traceback.format_exc()}")
        return ToolResult(
            tool_name=tool_name,
            success=False,
            error_message=f"{type(e).__name__}: {e}",
        )

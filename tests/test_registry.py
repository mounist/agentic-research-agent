"""Tests for tool registry dispatch."""
import pytest
from tools.registry import dispatch, TOOL_REGISTRY


class TestToolRegistry:
    def test_all_tools_registered(self):
        expected = {
            "get_price_data", "get_fundamentals", "get_earnings_data",
            "get_sector_peers", "get_earnings_transcript",
            "analyze_text_sentiment", "calculate_quant_signals",
            "query_research_memory", "save_research_memory",
            "search_transcript_passages",
        }
        assert set(TOOL_REGISTRY.keys()) == expected

    def test_dispatch_known_tool(self):
        result = dispatch("get_price_data", {"ticker": "AAPL"}, data_mode="mock")
        assert result.tool_name == "get_price_data"
        assert result.success is True
        assert result.data is not None
        assert result.data["ticker"] == "AAPL"

    def test_dispatch_unknown_tool(self):
        result = dispatch("nonexistent_tool", {}, data_mode="mock")
        assert result.success is False
        assert "Unknown tool" in result.error_message

    def test_dispatch_with_bad_params(self):
        """Tool should return error ToolResult, not crash."""
        result = dispatch("get_price_data", {"ticker": "ZZZZZZ"}, data_mode="mock")
        # No mock data for ZZZZZZ → should be a clean failure
        assert result.success is False

    def test_memory_tools_roundtrip(self):
        from memory.store import clear
        clear()

        # Save
        result = dispatch("save_research_memory", {
            "ticker": "TEST",
            "sector": "Technology",
            "recommendation": "buy",
            "confidence": 0.8,
            "key_findings": ["test"],
            "report_summary": "Test summary",
        }, data_mode="mock")
        assert result.success is True

        # Query
        result = dispatch("query_research_memory", {"ticker": "TEST"}, data_mode="mock")
        assert result.success is True
        assert result.data["n_results"] == 1

        clear()

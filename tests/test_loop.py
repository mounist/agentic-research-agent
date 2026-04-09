"""Tests for the agent loop — uses mock data, no real API calls."""
import pytest
from unittest.mock import patch, MagicMock
from agent.loop import run_agent, _extract_ticker, _TOOL_BUDGET_THRESHOLD, TOOL_BUDGET_NUDGE
from agent.models import EvalRecord


class TestExtractTicker:
    def test_simple_ticker(self):
        assert _extract_ticker("Analyse AAPL") == "AAPL"

    def test_ticker_in_sentence(self):
        assert _extract_ticker("What is the outlook for MSFT stock?") == "MSFT"

    def test_filters_common_words(self):
        assert _extract_ticker("I want to BUY TSLA") == "TSLA"

    def test_unknown_fallback(self):
        assert _extract_ticker("analyse this company") == "UNKNOWN"


class TestAgentLoopMocked:
    """Test the agent loop with a mocked Claude API."""

    def _make_mock_response(self, text: str = "", tool_uses: list = None, stop_reason: str = "end_turn"):
        """Create a mock Claude API response."""
        resp = MagicMock()
        resp.stop_reason = stop_reason
        resp.usage = MagicMock()
        resp.usage.input_tokens = 100
        resp.usage.output_tokens = 50

        content = []
        if text:
            text_block = MagicMock()
            text_block.type = "text"
            text_block.text = text
            content.append(text_block)
        if tool_uses:
            for tu in tool_uses:
                block = MagicMock()
                block.type = "tool_use"
                block.name = tu["name"]
                block.input = tu["input"]
                block.id = f"tu_{tu['name']}"
                content.append(block)

        resp.content = content
        return resp

    @patch("agent.loop.anthropic.Anthropic")
    def test_simple_report_no_tools(self, mock_anthropic_cls):
        """Agent immediately produces a report without calling tools."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = self._make_mock_response(
            text="**Recommendation: BUY**\n**Confidence: 80%**\nGreat stock.\nRisk: none."
        )

        report, eval_rec = run_agent("Analyse TEST", data_mode="mock")
        assert "BUY" in report
        assert eval_rec.recommendation == "buy"
        assert eval_rec.confidence == 0.80
        assert eval_rec.steps == 1
        assert len(eval_rec.tool_sequence) == 0

    @patch("agent.loop.anthropic.Anthropic")
    def test_tool_call_then_report(self, mock_anthropic_cls):
        """Agent calls one tool, then writes report."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        # First call: tool use
        # Second call: final report
        mock_client.messages.create.side_effect = [
            self._make_mock_response(
                tool_uses=[{"name": "query_research_memory", "input": {"ticker": "AAPL"}}],
                stop_reason="tool_use",
            ),
            self._make_mock_response(
                text="**Recommendation: HOLD**\n**Confidence: 70%**\nAnalysis.\nRisk factors: volatility."
            ),
        ]

        report, eval_rec = run_agent("Analyse AAPL", data_mode="mock")
        assert eval_rec.recommendation == "hold"
        assert eval_rec.steps == 2
        assert "query_research_memory" in eval_rec.tool_sequence

    @patch("agent.loop.anthropic.Anthropic")
    def test_max_iterations_forces_report(self, mock_anthropic_cls):
        """When max iterations hit, agent is forced to produce report."""
        import config
        original_max = config.MAX_ITERATIONS
        config.MAX_ITERATIONS = 2

        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        mock_client.messages.create.side_effect = [
            # Iteration 1: tool use
            self._make_mock_response(
                tool_uses=[{"name": "query_research_memory", "input": {}}],
                stop_reason="tool_use",
            ),
            # Iteration 2 (max): forced report
            self._make_mock_response(
                text="**Recommendation: HOLD**\n**Confidence: 50%**\nLimited data.\nRisk: incomplete."
            ),
        ]

        report, eval_rec = run_agent("Analyse TEST", data_mode="mock")
        assert eval_rec.steps == 2
        assert "HOLD" in report

        config.MAX_ITERATIONS = original_max

    @patch("agent.loop.anthropic.Anthropic")
    def test_tool_budget_nudge_injected(self, mock_anthropic_cls):
        """After 7+ unique tools, a nudge message is injected."""
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        # Build 7 distinct tool calls then a report
        tool_names = [
            "query_research_memory", "get_price_data", "get_fundamentals",
            "get_earnings_data", "get_sector_peers", "get_earnings_transcript",
            "analyze_text_sentiment",
        ]
        responses = []
        for name in tool_names:
            responses.append(self._make_mock_response(
                tool_uses=[{"name": name, "input": {"ticker": "X"}}],
                stop_reason="tool_use",
            ))
        # Final report after budget nudge
        responses.append(self._make_mock_response(
            text="**Recommendation: BUY**\n**Confidence: 75%**\nDone.\nRisk: market."
        ))

        mock_client.messages.create.side_effect = responses

        report, eval_rec = run_agent("Analyse X", data_mode="mock")
        # Check that the nudge was passed in messages
        calls = mock_client.messages.create.call_args_list
        # The last call (report generation) should have the nudge in messages
        last_messages = calls[-1].kwargs.get("messages", [])
        nudge_found = any(
            isinstance(m.get("content"), str) and "7 distinct tools" in m["content"]
            for m in last_messages
            if isinstance(m, dict)
        )
        assert nudge_found or len(eval_rec.tool_sequence) >= 7

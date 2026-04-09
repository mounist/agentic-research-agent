"""Tests for recommendation and confidence extraction from reports."""
import pytest
from agent.loop import _extract_recommendation, _extract_confidence


class TestExtractRecommendation:
    def test_explicit_buy(self):
        report = "**Recommendation: BUY**\n**Confidence: 85%**\nGreat stock."
        assert _extract_recommendation(report) == "buy"

    def test_explicit_hold(self):
        report = "**Recommendation: HOLD**\n**Confidence: 72%**\nFair value."
        assert _extract_recommendation(report) == "hold"

    def test_explicit_sell(self):
        report = "Recommendation: SELL\nConfidence: 60%\nOvervalued."
        assert _extract_recommendation(report) == "sell"

    def test_recommendation_with_dash(self):
        report = "Recommendation — HOLD\nConfidence: 68%"
        assert _extract_recommendation(report) == "hold"

    def test_xom_edge_case_hold_not_buy(self):
        """XOM report says HOLD in header but mentions BUY elsewhere."""
        report = (
            "## Executive Summary\n"
            "**Recommendation: HOLD**\n"
            "**Confidence: 72%**\n\n"
            "Some analysts argue investors should BUY on dips, but we "
            "believe the risk/reward is balanced. Commodity volatility "
            "makes a strong BUY case difficult.\n"
        )
        assert _extract_recommendation(report) == "hold"

    def test_sell_before_buy_in_header(self):
        """If SELL appears in header, don't match BUY mentioned later."""
        report = (
            "**Recommendation: SELL**\n"
            "Despite some who say BUY, we disagree.\n"
        )
        assert _extract_recommendation(report) == "sell"

    def test_fallback_to_head_500_chars(self):
        """Falls back to first 500 chars if no explicit pattern."""
        report = "# Report\nThis is a HOLD.\n" + "x" * 1000 + "\nBUY something else."
        assert _extract_recommendation(report) == "hold"

    def test_unknown_when_no_match(self):
        report = "This report has no recommendation at all."
        assert _extract_recommendation(report) == "unknown"


class TestExtractConfidence:
    def test_percentage(self):
        report = "**Confidence: 85%**"
        assert _extract_confidence(report) == 0.85

    def test_percentage_with_spaces(self):
        report = "Confidence:  72 %"
        assert _extract_confidence(report) == 0.72

    def test_decimal(self):
        report = "Confidence: 0.68"
        assert _extract_confidence(report) == 0.68

    def test_markdown_bold(self):
        report = "**Confidence: 90%**"
        assert _extract_confidence(report) == 0.90

    def test_no_confidence(self):
        report = "No confidence level stated."
        assert _extract_confidence(report) == 0.0

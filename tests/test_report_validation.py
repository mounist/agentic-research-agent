"""Tests for report structure validation."""
import pytest
from evaluation.metrics import validate_report_structure


class TestReportValidation:
    def test_valid_report(self):
        report = (
            "**Recommendation: BUY**\n"
            "**Confidence: 85%**\n\n"
            "## Key Findings\n"
            "Strong earnings growth and solid fundamentals.\n" * 20 + "\n"
            "## Risk Factors\n"
            "Market volatility and regulatory changes.\n"
        )
        result = validate_report_structure(report)
        assert result["is_valid"] is True
        assert result["has_recommendation"] is True
        assert result["has_confidence"] is True
        assert result["has_risk_section"] is True
        assert result["has_min_content"] is True

    def test_missing_recommendation(self):
        report = (
            "**Confidence: 85%**\n"
            "Some analysis here.\n" * 30 + "\n"
            "## Risk Factors\nSome risks.\n"
        )
        result = validate_report_structure(report)
        assert result["has_recommendation"] is False
        assert result["is_valid"] is False

    def test_missing_confidence(self):
        report = (
            "**Recommendation: BUY**\n"
            "Analysis.\n" * 30 + "\n"
            "## Risk Factors\nSome risks.\n"
        )
        result = validate_report_structure(report)
        assert result["has_confidence"] is False
        assert result["is_valid"] is False

    def test_missing_risk_section(self):
        report = (
            "**Recommendation: BUY**\n"
            "**Confidence: 85%**\n"
            "Analysis without any mention of dangers.\n" * 30
        )
        result = validate_report_structure(report)
        assert result["has_risk_section"] is False
        assert result["is_valid"] is False

    def test_too_short(self):
        report = "**Recommendation: BUY**\n**Confidence: 85%**\nRisk: low."
        result = validate_report_structure(report)
        assert result["has_min_content"] is False
        assert result["is_valid"] is False

    def test_report_length_tracked(self):
        report = "x" * 1234
        result = validate_report_structure(report)
        assert result["report_length"] == 1234

    def test_empty_report(self):
        result = validate_report_structure("")
        assert result["is_valid"] is False
        assert result["report_length"] == 0

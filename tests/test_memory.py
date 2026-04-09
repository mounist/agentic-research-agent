"""Tests for persistent memory store."""
import pytest
from memory.store import (
    save_research, query_by_ticker, query_by_sector, list_all, clear,
)


@pytest.fixture(autouse=True)
def clean_memory():
    """Clear memory before and after each test."""
    clear()
    yield
    clear()


class TestMemoryStore:
    def test_save_and_query_by_ticker(self):
        save_research({
            "ticker": "AAPL",
            "sector": "Technology",
            "recommendation": "buy",
            "confidence": 0.85,
            "key_findings": ["Strong iPhone sales"],
            "report_summary": "Apple is doing well.",
        })
        result = query_by_ticker("AAPL")
        assert result is not None
        assert result["ticker"] == "AAPL"
        assert result["recommendation"] == "buy"
        assert result["confidence"] == 0.85

    def test_query_nonexistent_ticker(self):
        result = query_by_ticker("ZZZZ")
        assert result is None

    def test_query_by_sector(self):
        save_research({"ticker": "AAPL", "sector": "Technology", "recommendation": "buy",
                       "confidence": 0.8, "key_findings": [], "report_summary": "x"})
        save_research({"ticker": "MSFT", "sector": "Technology", "recommendation": "hold",
                       "confidence": 0.7, "key_findings": [], "report_summary": "y"})
        save_research({"ticker": "JPM", "sector": "Financials", "recommendation": "buy",
                       "confidence": 0.75, "key_findings": [], "report_summary": "z"})

        tech = query_by_sector("Technology")
        assert len(tech) == 2
        assert all(r["sector"] == "Technology" for r in tech)

        fin = query_by_sector("Financials")
        assert len(fin) == 1

    def test_list_all(self):
        save_research({"ticker": "A", "sector": "X", "recommendation": "buy",
                       "confidence": 0.5, "key_findings": [], "report_summary": ""})
        save_research({"ticker": "B", "sector": "Y", "recommendation": "sell",
                       "confidence": 0.6, "key_findings": [], "report_summary": ""})
        assert len(list_all()) == 2

    def test_clear(self):
        save_research({"ticker": "A", "sector": "X", "recommendation": "buy",
                       "confidence": 0.5, "key_findings": [], "report_summary": ""})
        assert len(list_all()) == 1
        clear()
        assert len(list_all()) == 0

    def test_upsert_overwrites(self):
        save_research({"ticker": "AAPL", "sector": "Tech", "recommendation": "hold",
                       "confidence": 0.5, "key_findings": [], "report_summary": "old"})
        save_research({"ticker": "AAPL", "sector": "Tech", "recommendation": "buy",
                       "confidence": 0.9, "key_findings": [], "report_summary": "new"})
        result = query_by_ticker("AAPL")
        assert result["recommendation"] == "buy"
        assert result["confidence"] == 0.9
        assert len(list_all()) == 1

    def test_case_insensitive_ticker(self):
        save_research({"ticker": "aapl", "sector": "Tech", "recommendation": "buy",
                       "confidence": 0.5, "key_findings": [], "report_summary": ""})
        assert query_by_ticker("AAPL") is not None
        assert query_by_ticker("aapl") is not None

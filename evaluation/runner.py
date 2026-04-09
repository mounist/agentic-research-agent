"""
Evaluation runner — batch-execute the agent and collect structured results.

Usage:
    python -m evaluation.runner              # full eval (live mode)
    python -m evaluation.runner --mock       # mock mode
    python -m evaluation.runner --ticker AAPL # single ticker
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.loop import run_agent
from agent.models import EvalRecord
from evaluation.metrics import compute_summary, print_summary
from memory import store as memory_store
import config

logger = logging.getLogger(__name__)

# Tickers across different sectors
EVAL_TICKERS: list[str] = [
    "AAPL",  # Technology
    "JPM",   # Financials
    "JNJ",   # Healthcare
    "XOM",   # Energy
    "WMT",   # Consumer Staples
]

EVAL_QUERIES: dict[str, str] = {
    "AAPL": "Analyse Apple (AAPL): recent earnings performance, price momentum, and outlook. Should I buy, hold, or sell?",
    "JPM": "Analyse JPMorgan Chase (JPM): credit quality, earnings trends, and valuation. Provide a recommendation.",
    "JNJ": "Analyse Johnson & Johnson (JNJ): pharmaceutical pipeline strength, margin trends, and risk factors.",
    "XOM": "Analyse Exxon Mobil (XOM): production trends, earnings volatility, and whether the stock is fairly valued.",
    "WMT": "Analyse Walmart (WMT): e-commerce growth, margin expansion, and competitive positioning.",
}


def run_evaluation(
    tickers: list[str] | None = None,
    data_mode: str = "mock",
    include_repeat_test: bool = True,
) -> list[dict]:
    """Run full evaluation suite. Returns list of EvalRecord dicts."""
    tickers = tickers or EVAL_TICKERS
    all_records: list[EvalRecord] = []

    # Clear memory for clean eval
    memory_store.clear()
    print(f"\n{'='*70}")
    print(f"  FinAgent Evaluation Suite — {data_mode.upper()} mode")
    print(f"  {len(tickers)} tickers" + (" + repeat test" if include_repeat_test else ""))
    print(f"{'='*70}\n")

    # Phase 1: First pass on all tickers
    for i, ticker in enumerate(tickers, 1):
        query = EVAL_QUERIES.get(ticker, f"Analyse {ticker} and provide a buy/hold/sell recommendation.")
        print(f"[{i}/{len(tickers)}] Researching {ticker} (first run)...")

        try:
            report, eval_rec = run_agent(query, data_mode=data_mode)
            eval_rec.run_label = "first_run"
            all_records.append(eval_rec)
            print(f"  -> {eval_rec.steps} steps, {len(eval_rec.tool_sequence)} tool calls, "
                  f"{eval_rec.total_tokens} tokens, {eval_rec.latency_seconds:.1f}s, "
                  f"rec={eval_rec.recommendation}")
        except Exception as e:
            print(f"  -> FAILED: {e}")
            rec = EvalRecord(ticker=ticker, query=query, run_label="first_run")
            rec.final_report = f"Error: {e}"
            all_records.append(rec)

    # Phase 2: Repeat test — run first ticker again to prove memory-aware divergence
    if include_repeat_test and tickers:
        repeat_ticker = tickers[0]
        query = EVAL_QUERIES.get(repeat_ticker, f"Analyse {repeat_ticker}.")
        print(f"\n--- REPEAT TEST: {repeat_ticker} (second run, memory should change behavior) ---")

        try:
            report, eval_rec = run_agent(query, data_mode=data_mode)
            eval_rec.run_label = "second_run_memory"
            all_records.append(eval_rec)
            print(f"  -> {eval_rec.steps} steps, {len(eval_rec.tool_sequence)} tool calls, "
                  f"{eval_rec.total_tokens} tokens, {eval_rec.latency_seconds:.1f}s, "
                  f"rec={eval_rec.recommendation}")
        except Exception as e:
            print(f"  -> FAILED: {e}")

    # Save results
    results = [r.to_dict() for r in all_records]
    output = {
        "evaluation_date": datetime.now(timezone.utc).isoformat(),
        "data_mode": data_mode,
        "n_tickers": len(tickers),
        "results": results,
    }

    output_path = config.OUTPUT_DIR / "evaluation_results.json"
    output_path.write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
    print(f"\nResults saved to {output_path}")

    # Print summary
    summary = compute_summary(all_records)
    output["summary"] = summary
    output_path.write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
    print_summary(all_records, summary)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="FinAgent evaluation runner")
    parser.add_argument("--mock", action="store_true", help="Use mock data")
    parser.add_argument("--live", action="store_true", help="Use live WRDS data")
    parser.add_argument("--ticker", type=str, help="Run single ticker only")
    parser.add_argument("--no-repeat", action="store_true", help="Skip repeat test")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")

    data_mode = "live" if args.live else "mock"
    tickers = [args.ticker.upper()] if args.ticker else None

    run_evaluation(
        tickers=tickers,
        data_mode=data_mode,
        include_repeat_test=not args.no_repeat,
    )


if __name__ == "__main__":
    main()

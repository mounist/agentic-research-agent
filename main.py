"""
FinAgent — Autonomous Equity Research Agent with Persistent Memory.

Usage:
    python main.py "Analyse AAPL's recent earnings and outlook"          # live WRDS (default)
    python main.py --mock "Analyse AAPL's recent earnings and outlook"   # credential-free mock
    python main.py --evaluate                                            # evaluation suite (live)
    python main.py --evaluate --mock                                     # evaluation suite (mock)
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="FinAgent — Autonomous Equity Research Agent",
    )
    parser.add_argument("query", nargs="?", help="Research query, e.g. 'Analyse AAPL'")
    parser.add_argument("--live", action="store_true", default=False, help="Use live WRDS data (default)")
    parser.add_argument("--mock", action="store_true", help="Use credential-free mock data")
    parser.add_argument("--evaluate", action="store_true", help="Run evaluation suite")
    parser.add_argument("--ticker", type=str, help="Single ticker for evaluation")
    parser.add_argument(
        "--index-transcripts",
        action="store_true",
        help="Build (or rebuild) the RAG vector index over mock transcripts, then exit.",
    )
    parser.add_argument("--langgraph", action="store_true", help="Use LangGraph-based agent loop instead of the manual while-loop")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    data_mode = "mock" if args.mock else "live"

    if args.index_transcripts:
        from rag.indexer import build_index
        print(f"Building RAG transcript index ({data_mode} mode)...")
        n = build_index(rebuild=True, data_mode=data_mode)
        print(f"Indexed {n} chunks.")
        return

    # Auto-build index on first run if missing (mock mode only — live requires explicit build)
    if data_mode == "mock":
        try:
            from rag.indexer import index_exists, build_index
            if not index_exists():
                print("RAG index not found — building on first run (this takes ~30s)...")
                build_index(data_mode="mock")
        except ImportError:
            pass  # RAG deps optional; tool will surface error if invoked

    if args.evaluate:
        from evaluation.runner import run_evaluation
        tickers = [args.ticker.upper()] if args.ticker else None
        run_evaluation(tickers=tickers, data_mode=data_mode, use_langgraph=args.langgraph)
        return

    if not args.query:
        parser.print_help()
        print("\nExample: python main.py \"Analyse AAPL's recent earnings and outlook\"")
        sys.exit(1)

    # Single research run
    if args.langgraph:
        from agent.loop_langgraph import run_agent_langgraph as run_agent
        impl_label = "LangGraph"
    else:
        from agent.loop import run_agent
        impl_label = "manual loop"
    print(f"FinAgent — {data_mode.upper()} mode ({impl_label})")
    print(f"Query: {args.query}\n")

    report, eval_rec = run_agent(args.query, data_mode=data_mode)

    print("\n" + "=" * 70)
    print("  RESEARCH REPORT")
    print("=" * 70)
    print(report)
    print("=" * 70)
    print(f"\nStats: {eval_rec.steps} steps, {len(eval_rec.tool_sequence)} tool calls, "
          f"{eval_rec.total_tokens} tokens, {eval_rec.latency_seconds:.1f}s")
    print(f"Tools used: {' -> '.join(eval_rec.tool_sequence)}")


if __name__ == "__main__":
    main()

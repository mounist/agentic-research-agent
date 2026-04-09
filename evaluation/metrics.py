"""Evaluation metrics and analysis — compute summaries from EvalRecords."""
from __future__ import annotations

from collections import Counter
from typing import Any

from agent.models import EvalRecord


def compute_summary(records: list[EvalRecord]) -> dict[str, Any]:
    """Compute aggregate metrics from a list of eval records."""
    if not records:
        return {}

    first_runs = [r for r in records if r.run_label == "first_run"]
    repeat_runs = [r for r in records if r.run_label == "second_run_memory"]

    # Basic stats
    steps = [r.steps for r in first_runs]
    tokens = [r.total_tokens for r in first_runs]
    latencies = [r.latency_seconds for r in first_runs]

    summary: dict[str, Any] = {
        "n_tickers": len(first_runs),
        "steps": {
            "mean": _mean(steps),
            "median": _median(steps),
            "min": min(steps) if steps else 0,
            "max": max(steps) if steps else 0,
        },
        "tokens": {
            "mean": _mean(tokens),
            "median": _median(tokens),
            "min": min(tokens) if tokens else 0,
            "max": max(tokens) if tokens else 0,
        },
        "latency_seconds": {
            "mean": round(_mean(latencies), 1),
            "median": round(_median(latencies), 1),
            "min": round(min(latencies), 1) if latencies else 0,
            "max": round(max(latencies), 1) if latencies else 0,
        },
        "recommendations": dict(Counter(r.recommendation for r in first_runs)),
    }

    # Tool usage distribution
    all_tools = []
    for r in first_runs:
        all_tools.extend(r.tool_sequence)
    summary["tool_usage_distribution"] = dict(Counter(all_tools).most_common())

    # Per-ticker tool sequences
    summary["per_ticker_sequences"] = {
        r.ticker: r.tool_sequence for r in first_runs
    }

    # Path diversity: how many unique tool sequences?
    unique_seqs = set(tuple(r.tool_sequence) for r in first_runs)
    summary["path_diversity"] = {
        "unique_sequences": len(unique_seqs),
        "total_runs": len(first_runs),
        "diversity_ratio": round(len(unique_seqs) / max(len(first_runs), 1), 2),
    }

    # Memory test comparison
    if repeat_runs and first_runs:
        repeat = repeat_runs[0]
        # Find the matching first run
        first = next((r for r in first_runs if r.ticker == repeat.ticker), None)
        if first:
            summary["memory_test"] = {
                "ticker": repeat.ticker,
                "first_run_tools": first.tool_sequence,
                "second_run_tools": repeat.tool_sequence,
                "first_run_steps": first.steps,
                "second_run_steps": repeat.steps,
                "first_run_tokens": first.total_tokens,
                "second_run_tokens": repeat.total_tokens,
                "sequences_differ": first.tool_sequence != repeat.tool_sequence,
                "tools_only_in_first": list(set(first.tool_sequence) - set(repeat.tool_sequence)),
                "tools_only_in_second": list(set(repeat.tool_sequence) - set(first.tool_sequence)),
            }

    return summary


def print_summary(records: list[EvalRecord], summary: dict[str, Any]) -> None:
    """Print a human-readable summary table."""
    print(f"\n{'='*70}")
    print("  EVALUATION SUMMARY")
    print(f"{'='*70}")

    # Per-ticker table
    print(f"\n{'Ticker':<8} {'Run':<18} {'Steps':>5} {'Tools':>5} {'Tokens':>8} "
          f"{'Latency':>8} {'Rec':<6}")
    print("-" * 70)
    for r in records:
        print(f"{r.ticker:<8} {r.run_label:<18} {r.steps:>5} "
              f"{len(r.tool_sequence):>5} {r.total_tokens:>8} "
              f"{r.latency_seconds:>7.1f}s {r.recommendation:<6}")

    # Aggregates
    s = summary
    print(f"\n--- Aggregates (first runs only) ---")
    print(f"  Steps:   mean={s['steps']['mean']:.1f}, "
          f"median={s['steps']['median']:.1f}, range=[{s['steps']['min']}-{s['steps']['max']}]")
    print(f"  Tokens:  mean={s['tokens']['mean']:.0f}, "
          f"median={s['tokens']['median']:.0f}")
    print(f"  Latency: mean={s['latency_seconds']['mean']:.1f}s, "
          f"median={s['latency_seconds']['median']:.1f}s")

    # Path diversity
    pd = s.get("path_diversity", {})
    print(f"\n--- Path Diversity ---")
    print(f"  {pd.get('unique_sequences', 0)}/{pd.get('total_runs', 0)} unique tool sequences "
          f"(diversity ratio: {pd.get('diversity_ratio', 0):.0%})")

    # Tool usage
    print(f"\n--- Tool Usage Distribution ---")
    for tool, count in s.get("tool_usage_distribution", {}).items():
        print(f"  {tool:<30} {count:>4} calls")

    # Memory test
    mt = s.get("memory_test")
    if mt:
        print(f"\n--- Memory Test ({mt['ticker']}) ---")
        print(f"  First run:  {mt['first_run_steps']} steps, tools: {mt['first_run_tools']}")
        print(f"  Second run: {mt['second_run_steps']} steps, tools: {mt['second_run_tools']}")
        print(f"  Sequences differ: {mt['sequences_differ']}")
        if mt.get("tools_only_in_first"):
            print(f"  Tools only in first run:  {mt['tools_only_in_first']}")
        if mt.get("tools_only_in_second"):
            print(f"  Tools only in second run: {mt['tools_only_in_second']}")

    print(f"\n{'='*70}\n")


def _mean(vals: list[int | float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def _median(vals: list[int | float]) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    n = len(s)
    if n % 2 == 0:
        return (s[n // 2 - 1] + s[n // 2]) / 2
    return float(s[n // 2])

"""Data models for agent state, tool results, and evaluation records."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Standardised wrapper returned by every tool."""
    tool_name: str
    success: bool
    data: dict[str, Any] | None = None
    error_message: str | None = None

    def to_content_str(self) -> str:
        """Serialise for inclusion in Claude messages."""
        import json
        if self.success:
            return json.dumps(self.data, default=str)
        return f"Error: {self.error_message}"


@dataclass
class AgentState:
    """Accumulated context for a single research run."""
    query: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    tool_trace: list[dict[str, Any]] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    iteration: int = 0
    start_time: float = field(default_factory=time.time)
    final_report: str | None = None

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time

    def record_tool_call(self, tool_name: str, params: dict, result: ToolResult) -> None:
        self.tool_trace.append({
            "step": self.iteration,
            "tool": tool_name,
            "params": {k: v for k, v in params.items() if k != "text"},  # skip large text
            "success": result.success,
        })


@dataclass
class EvalRecord:
    """Metadata captured per run for the evaluation suite."""
    ticker: str
    query: str
    steps: int = 0
    tool_sequence: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_seconds: float = 0.0
    recommendation: str = ""
    confidence: float = 0.0
    final_report: str = ""
    run_label: str = ""  # e.g. "first_run" or "second_run"

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "query": self.query,
            "run_label": self.run_label,
            "steps": self.steps,
            "tool_sequence": self.tool_sequence,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "latency_seconds": round(self.latency_seconds, 2),
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "final_report": self.final_report,
        }

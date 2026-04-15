"""
LangGraph-based reimplementation of the agent loop.

Expresses the same ReAct-style behavior as `agent/loop.py`, but as a
`StateGraph` with explicit `reason` and `tool` nodes plus conditional
edges. Functionally equivalent — same system prompt, same tool schemas,
same dispatch logic, same stop conditions, same budget nudge threshold.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

from agent.loop import (
    TOOL_BUDGET_NUDGE,
    _TOOL_BUDGET_THRESHOLD,
    _call_claude_with_retry,
    _extract_confidence,
    _extract_recommendation,
    _extract_ticker,
)
from agent.models import EvalRecord, ToolResult
from agent.prompts import FORCE_REPORT_PROMPT, SYSTEM_PROMPT, TOOL_SCHEMAS
from tools.registry import dispatch
import config

logger = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    """LangGraph state — raw tracking fields only; EvalRecord assembled later."""
    query: str
    data_mode: str
    messages: list[dict[str, Any]]
    tool_sequence: list[str]
    iteration_count: int
    input_tokens: int
    output_tokens: int
    final_report: str | None
    # Transient: carried from reason_node to tool_node within one tick.
    pending_tool_uses: list[Any]
    pending_assistant_content: Any


def reason_node(state: AgentState) -> dict[str, Any]:
    """One Claude API call. Handles first-iteration planning, mid-run tool
    budget nudges, and the final forced-report iteration, mirroring
    `agent/loop.py`'s while-loop body."""
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    iteration = state.get("iteration_count", 0) + 1
    logger.info(f"--- Iteration {iteration} (langgraph) ---")

    messages = list(state["messages"])

    if iteration == config.MAX_ITERATIONS:
        messages.append({"role": "user", "content": FORCE_REPORT_PROMPT})

    unique_tools = set(state.get("tool_sequence", []))
    if (
        len(unique_tools) >= _TOOL_BUDGET_THRESHOLD
        and iteration < config.MAX_ITERATIONS
    ):
        messages.append({
            "role": "user",
            "content": TOOL_BUDGET_NUDGE.format(n=len(unique_tools)),
        })

    response = _call_claude_with_retry(
        client,
        model=config.AGENT_MODEL,
        max_tokens=config.MAX_TOKENS,
        system=SYSTEM_PROMPT,
        tools=TOOL_SCHEMAS,
        messages=messages,
    )

    tool_uses = [b for b in response.content if b.type == "tool_use"]
    text_parts = [b.text for b in response.content if b.type == "text"]

    update: dict[str, Any] = {
        "iteration_count": iteration,
        "input_tokens": state.get("input_tokens", 0) + response.usage.input_tokens,
        "output_tokens": state.get("output_tokens", 0) + response.usage.output_tokens,
    }

    if response.stop_reason == "end_turn" and not tool_uses:
        update["final_report"] = "\n".join(text_parts)
        update["pending_tool_uses"] = []
        logger.info("Agent produced final report.")
        return update

    if tool_uses:
        update["messages"] = state["messages"] + [
            {"role": "assistant", "content": response.content}
        ]
        update["pending_tool_uses"] = tool_uses
        update["pending_assistant_content"] = response.content
        return update

    # Text-only response without end_turn — treat as final (rare).
    update["final_report"] = "\n".join(text_parts) if text_parts else "No report generated."
    update["pending_tool_uses"] = []
    return update


def tool_node(state: AgentState) -> dict[str, Any]:
    """Dispatch every tool_use block via the shared `dispatch()` function
    from `tools.registry`, then append the aggregated tool_result user
    message to state.messages."""
    tool_uses = state.get("pending_tool_uses") or []
    data_mode = state.get("data_mode", "live")
    tool_sequence = list(state.get("tool_sequence", []))

    tool_results_content = []
    for tu in tool_uses:
        logger.info(
            f"  Tool call: {tu.name}({json.dumps(tu.input, default=str)[:200]})"
        )
        result: ToolResult = dispatch(tu.name, tu.input, data_mode=data_mode)
        tool_sequence.append(tu.name)
        tool_results_content.append({
            "type": "tool_result",
            "tool_use_id": tu.id,
            "content": result.to_content_str(),
        })

    return {
        "messages": state["messages"] + [
            {"role": "user", "content": tool_results_content}
        ],
        "tool_sequence": tool_sequence,
        "pending_tool_uses": [],
    }


def _after_reason(state: AgentState) -> str:
    """Route to tool_node if the LLM requested tool calls, else END."""
    if state.get("final_report") is not None:
        return "end"
    if state.get("pending_tool_uses"):
        return "tools"
    return "end"


def _build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("reason", reason_node)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "reason")
    graph.add_conditional_edges(
        "reason",
        _after_reason,
        {"tools": "tools", "end": END},
    )
    graph.add_edge("tools", "reason")
    return graph.compile()


_GRAPH = None


def _get_graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = _build_graph()
    return _GRAPH


def run_agent_langgraph(
    query: str, data_mode: str = "live"
) -> tuple[str, EvalRecord]:
    """Execute the LangGraph agent for a single research query.

    Same return signature as `agent.loop.run_agent`.
    """
    t0 = time.time()
    initial_state: AgentState = {
        "query": query,
        "data_mode": data_mode,
        "messages": [{"role": "user", "content": query}],
        "tool_sequence": [],
        "iteration_count": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "final_report": None,
    }

    graph = _get_graph()
    final_state: AgentState = graph.invoke(
        initial_state,
        config={"recursion_limit": config.MAX_ITERATIONS * 2 + 5},
    )

    final_report = final_state.get("final_report") or (
        "Max iterations reached. No report produced."
    )

    eval_rec = EvalRecord(ticker=_extract_ticker(query), query=query)
    eval_rec.steps = final_state.get("iteration_count", 0)
    eval_rec.tool_sequence = list(final_state.get("tool_sequence", []))
    eval_rec.input_tokens = final_state.get("input_tokens", 0)
    eval_rec.output_tokens = final_state.get("output_tokens", 0)
    eval_rec.total_tokens = eval_rec.input_tokens + eval_rec.output_tokens
    eval_rec.latency_seconds = time.time() - t0
    eval_rec.final_report = final_report
    eval_rec.recommendation = _extract_recommendation(final_report)
    eval_rec.confidence = _extract_confidence(final_report)

    return final_report, eval_rec

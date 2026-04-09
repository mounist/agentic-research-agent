"""
The core agent loop — the heart of FinAgent.

ReAct-style loop using Claude's tool_use API. Claude decides what tool
to call at each step based on accumulated evidence. The loop exits when
Claude produces a text-only response (the final research report) or
when the iteration limit is reached.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import anthropic

from agent.models import AgentState, EvalRecord, ToolResult
from agent.prompts import FORCE_REPORT_PROMPT, SYSTEM_PROMPT, TOOL_SCHEMAS
from tools.registry import dispatch
import config

logger = logging.getLogger(__name__)


def run_agent(query: str, data_mode: str = "mock") -> tuple[str, EvalRecord]:
    """
    Execute the full agent loop for a single research query.

    Returns (final_report_text, eval_record).
    """
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    state = AgentState(query=query)

    # Initial user message
    state.messages = [{"role": "user", "content": query}]

    eval_rec = EvalRecord(ticker=_extract_ticker(query), query=query)

    while state.iteration < config.MAX_ITERATIONS:
        state.iteration += 1
        logger.info(f"--- Iteration {state.iteration} ---")

        # If at max iterations, force a report
        messages = list(state.messages)
        if state.iteration == config.MAX_ITERATIONS:
            messages.append({"role": "user", "content": FORCE_REPORT_PROMPT})

        # Call Claude
        response = client.messages.create(
            model=config.AGENT_MODEL,
            max_tokens=config.MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        # Track tokens
        state.input_tokens += response.usage.input_tokens
        state.output_tokens += response.usage.output_tokens

        # Parse response content blocks
        tool_uses = []
        text_parts = []

        for block in response.content:
            if block.type == "tool_use":
                tool_uses.append(block)
            elif block.type == "text":
                text_parts.append(block.text)

        # If stop_reason is "end_turn" and no tool_use → final report
        if response.stop_reason == "end_turn" and not tool_uses:
            final_report = "\n".join(text_parts)
            state.final_report = final_report
            logger.info("Agent produced final report.")
            break

        # If there are tool uses, dispatch them
        if tool_uses:
            # Append assistant message with all content blocks
            state.messages.append({"role": "assistant", "content": response.content})

            # Process each tool call
            tool_results_content = []
            for tu in tool_uses:
                tool_name = tu.name
                tool_input = tu.input
                logger.info(f"  Tool call: {tool_name}({json.dumps(tool_input, default=str)[:200]})")

                result: ToolResult = dispatch(tool_name, tool_input, data_mode=data_mode)
                state.record_tool_call(tool_name, tool_input, result)
                eval_rec.tool_sequence.append(tool_name)

                tool_results_content.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": result.to_content_str(),
                })

            state.messages.append({"role": "user", "content": tool_results_content})
        else:
            # Text response but stop_reason wasn't end_turn (shouldn't happen often)
            final_report = "\n".join(text_parts) if text_parts else "No report generated."
            state.final_report = final_report
            break
    else:
        # Exhausted iterations without a report — use last text if any
        state.final_report = state.final_report or "Max iterations reached. No report produced."

    # Build eval record
    eval_rec.steps = state.iteration
    eval_rec.input_tokens = state.input_tokens
    eval_rec.output_tokens = state.output_tokens
    eval_rec.total_tokens = state.input_tokens + state.output_tokens
    eval_rec.latency_seconds = state.elapsed
    eval_rec.final_report = state.final_report or ""
    eval_rec.recommendation = _extract_recommendation(eval_rec.final_report)
    eval_rec.confidence = _extract_confidence(eval_rec.final_report)

    return state.final_report or "", eval_rec


def _extract_ticker(query: str) -> str:
    """Best-effort ticker extraction from a natural language query."""
    import re
    # Look for uppercase 1-5 letter words that look like tickers
    tokens = re.findall(r"\b([A-Z]{1,5})\b", query)
    # Filter out common English words
    skip = {"A", "I", "AN", "AS", "AT", "BE", "BY", "DO", "GO", "IF", "IN",
            "IS", "IT", "MY", "NO", "OF", "ON", "OR", "SO", "TO", "UP", "US",
            "WE", "AND", "THE", "FOR", "BUT", "NOT", "YOU", "ALL", "CAN",
            "HER", "WAS", "ONE", "OUR", "OUT", "BUY", "SELL", "HOLD"}
    for t in tokens:
        if t not in skip:
            return t
    return "UNKNOWN"


def _extract_recommendation(report: str) -> str:
    """Extract BUY/HOLD/SELL from the structured recommendation header.

    Looks for explicit patterns like:
      'Recommendation: BUY', '**Recommendation: HOLD**',
      'RECOMMENDATION: SELL', 'Recommendation — BUY'
    Falls back to 'Executive Summary' section if no direct match.
    """
    import re
    # Pattern 1: explicit "Recommendation: X" line (strongest signal)
    match = re.search(
        r"recommendation[:\s*—\-]+\*{0,2}\s*(BUY|SELL|HOLD)",
        report, re.IGNORECASE,
    )
    if match:
        return match.group(1).lower()

    # Pattern 2: look only in the first 500 chars (executive summary area)
    head = report[:500].upper()
    for rec in ["SELL", "HOLD", "BUY"]:  # check SELL/HOLD first to avoid false BUY matches
        if rec in head:
            return rec.lower()

    return "unknown"


def _extract_confidence(report: str) -> float:
    """Extract confidence percentage from the structured header or nearby text."""
    import re
    # Pattern 1: "Confidence: 75%" or "**Confidence: 75%**"
    match = re.search(r"confidence[:\s*]+(\d{1,3})\s*%", report, re.IGNORECASE)
    if match:
        return float(match.group(1)) / 100.0
    # Pattern 2: decimal "confidence: 0.75"
    match = re.search(r"confidence[:\s*]+(0\.\d+)", report, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return 0.0

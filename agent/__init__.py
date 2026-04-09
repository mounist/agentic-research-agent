"""
agent — Core orchestration layer.

This package contains the agentic loop that drives FinAgent.
The LLM (Claude) receives the user query, current gathered context, and
available tools, then autonomously decides which tool to call next.
The loop continues until the agent produces a final research report
or hits the max-iteration safety limit.
"""

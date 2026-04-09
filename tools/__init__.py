"""
tools — Implementations of every tool the agent can invoke.

Each module exposes a single function matching the tool name.
All functions accept a dict of parameters (from Claude's tool_use input)
and return a ToolResult.  The registry module maps tool names to their
implementations so the agent loop can dispatch dynamically.
"""

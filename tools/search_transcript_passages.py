"""Tool: search_transcript_passages — cross-quarter semantic retrieval."""
from __future__ import annotations

from typing import Any

from agent.models import ToolResult


def search_transcript_passages(
    ticker: str,
    query: str,
    top_k: int = 5,
    data_mode: str = "mock",
    **kwargs: Any,
) -> ToolResult:
    """
    Semantic search over 8 quarters of earnings transcripts for `ticker`.

    Useful for multi-quarter qualitative analysis: margin trajectory, tone
    shifts, strategic pivots, guidance evolution.
    """
    try:
        from rag.retriever import search_passages
        from rag.indexer import index_exists, build_index
    except ImportError as e:
        return ToolResult(
            tool_name="search_transcript_passages",
            success=False,
            error_message=f"RAG dependencies not installed: {e}. Run pip install -r requirements.txt.",
        )

    if not index_exists():
        try:
            n = build_index()
            if n == 0:
                return ToolResult(
                    tool_name="search_transcript_passages",
                    success=False,
                    error_message="No transcripts available to index.",
                )
        except Exception as e:
            return ToolResult(
                tool_name="search_transcript_passages",
                success=False,
                error_message=f"Index build failed: {type(e).__name__}: {e}",
            )

    top_k = max(1, min(int(top_k), 15))
    passages = search_passages(ticker.upper(), query, top_k=top_k)

    if not passages:
        return ToolResult(
            tool_name="search_transcript_passages",
            success=False,
            error_message=f"No transcript passages found for {ticker}.",
        )

    # Truncate each passage's text for token budget
    for p in passages:
        if len(p["text"]) > 1200:
            p["text"] = p["text"][:1200] + " [...]"

    return ToolResult(
        tool_name="search_transcript_passages",
        success=True,
        data={
            "ticker": ticker.upper(),
            "query": query,
            "n_results": len(passages),
            "passages": passages,
        },
    )

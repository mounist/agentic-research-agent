"""Tool: analyze_text_sentiment — Claude-based financial sentiment analysis."""
from __future__ import annotations

import json
import logging
from typing import Any

from agent.models import ToolResult
import config

logger = logging.getLogger(__name__)

_SENTIMENT_PROMPT = """\
You are a financial sentiment analyst. Analyse the following earnings call \
transcript excerpt and return a JSON object with exactly these fields:

{
  "overall_sentiment": "bullish" | "bearish" | "neutral" | "mixed",
  "confidence": <float 0-1>,
  "key_themes": [<list of 3-5 major topics discussed>],
  "management_tone": "<one sentence describing management's tone>",
  "forward_guidance": "<one paragraph summarising forward-looking statements>",
  "risks_mentioned": [<list of risks discussed>],
  "notable_quotes": [<2-3 verbatim quotes that most inform the sentiment>]
}

Return ONLY the JSON object, no other text.
"""


def analyze_text_sentiment(
    text: str = "",
    context: str = "",
    data_mode: str = "mock",
    **kwargs: Any,
) -> ToolResult:
    """Analyse financial text sentiment using Claude."""
    # Claude may pass text under a different key
    if not text:
        text = kwargs.get("transcript_text", "") or kwargs.get("content", "")
    if not text or len(text.strip()) < 50:
        return ToolResult(
            tool_name="analyze_text_sentiment",
            success=False,
            error_message="Text too short for meaningful analysis.",
        )

    # Truncate to avoid blowing context budget
    if len(text) > 12000:
        text = text[:12000] + "\n[truncated]"

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

        user_msg = f"Context: {context}\n\nTranscript:\n{text}" if context else text

        response = client.messages.create(
            model=config.SENTIMENT_MODEL,
            max_tokens=1024,
            system=_SENTIMENT_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )

        raw = response.content[0].text.strip()
        # Parse JSON — handle markdown code fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw)

        return ToolResult(
            tool_name="analyze_text_sentiment",
            success=True,
            data=result,
        )

    except json.JSONDecodeError as e:
        logger.warning(f"Sentiment JSON parse error: {e}")
        return ToolResult(
            tool_name="analyze_text_sentiment",
            success=True,
            data={
                "overall_sentiment": "unknown",
                "confidence": 0.0,
                "raw_response": raw if "raw" in dir() else "",
                "parse_error": str(e),
            },
        )
    except Exception as e:
        return ToolResult(
            tool_name="analyze_text_sentiment",
            success=False,
            error_message=f"Sentiment analysis failed: {e}",
        )

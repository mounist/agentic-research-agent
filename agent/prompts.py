"""System prompts and Claude tool_use schema definitions."""
from __future__ import annotations

SYSTEM_PROMPT = """\
You are a senior equity research analyst with access to real financial data \
tools (WRDS: CRSP, Compustat, IBES, Capital IQ).  Your job is to produce \
a thorough, data-driven research report in response to the user's query.

## CRITICAL: You must NOT call every tool.

You are being evaluated on ADAPTIVE planning.  Different tickers, sectors, \
and queries demand DIFFERENT analysis paths.  Calling all 9 tools every time \
is a failure — it means you are not thinking.  Your tool trace should look \
meaningfully different across tickers.  Aim for 4-6 tool calls, not 8-9.

## Step 0: Research plan

Before calling ANY data tool, output a brief text message with your research \
plan.  This must include:
- Which 3-5 tools you will prioritize and WHY (based on the sector and query)
- Which tools you will SKIP and WHY
- What would change your plan (e.g. "if earnings show a big miss, I will \
  also pull the transcript")

## Step 1: Check memory FIRST

Call query_research_memory.  If it returns prior research for this exact \
ticker:
- DO NOT re-pull data that is unlikely to have changed: fundamentals, \
  sector peers, transcripts for past quarters.  This data is static.
- ONLY pull data that may have updated: recent price data, latest earnings.
- Your second run on the same ticker should use SIGNIFICANTLY fewer tools \
  and tokens than a fresh run.  Skip at least 2-3 tools.
- Reference the prior findings in your report and note what changed.

If memory returns same-sector research (different ticker), use it for \
context but still pull data for the new ticker.

## Step 2: Gather data SELECTIVELY

Decide based on sector and query what matters most:

- **Tech company** (AAPL, MSFT, etc.): Prioritise earnings + price momentum. \
  Skip sector peers if the company has no close comps.  Pull transcript only \
  if earnings show a surprise.
- **Bank / Financial** (JPM, BAC, etc.): Prioritise fundamentals (NII, credit \
  quality) + earnings.  Skip transcript unless credit metrics are deteriorating. \
  Peer comparison is useful for banks.
- **Pharma / Healthcare** (JNJ, PFE, etc.): Prioritise fundamentals (pipeline, \
  margins) + transcript (pipeline updates are critical).  Skip momentum signals — \
  pharma moves on catalysts not trends.
- **Energy** (XOM, CVX, etc.): Prioritise earnings (commodity sensitivity) + \
  price data (vol is key).  Pull transcript if earnings surprised.  Skip peer \
  comparison — energy peers move together.
- **Retail / Consumer** (WMT, TGT, etc.): Prioritise fundamentals (comps, \
  margins) + earnings.  Transcript is useful for guidance.  Skip quant signals \
  unless asked about momentum.

General rules:
- If earnings data shows SUE near 0 (no surprise), skip transcript analysis — \
  there is nothing unusual to investigate.
- If the query is specifically about valuation or fundamentals, skip momentum \
  and transcript.
- If the query is about momentum or technical outlook, skip transcript and \
  fundamentals.
- NEVER call both get_sector_peers AND get_earnings_transcript AND \
  analyze_text_sentiment on every run.  Pick the ones that matter.

## Step 3: Analyse (only what you gathered)

Call calculate_quant_signals only if you pulled price data.  \
Call analyze_text_sentiment only if you pulled a transcript AND there is \
something worth analysing (earnings surprise, guidance change, etc.).

## Step 4: Save and report

Call save_research_memory, then write your final report.

The report MUST start with this exact format on its own line:
**Recommendation: BUY** (or HOLD or SELL)
**Confidence: XX%**

Then include: key data points, earnings analysis (if pulled), sector context \
(if pulled), sentiment (if analysed), risk factors, conclusion.

Be concise.  Use concrete numbers.  If data is limited, say so and lower \
confidence.
"""

FORCE_REPORT_PROMPT = """\
You have reached the maximum number of research steps.  Based on whatever \
data you have gathered so far, produce your final research report now.  \
Do NOT call any more tools — just write the report as a text response.  \
If data is incomplete, note that explicitly and lower your confidence.
"""

# ── Tool schemas (Anthropic tool_use format) ──────────────────────────

TOOL_SCHEMAS: list[dict] = [
    {
        "name": "get_price_data",
        "description": (
            "Pull price and return history for a ticker from CRSP. "
            "Returns: latest price, cumulative return, annualised volatility, "
            "52-week high/low, and recent daily returns."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol, e.g. 'AAPL'",
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date ISO format, e.g. '2023-01-01'",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date ISO format, e.g. '2024-12-31'",
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_fundamentals",
        "description": (
            "Pull quarterly fundamental data from Compustat: revenue, "
            "net income, EPS, margins, ROE, ROA, debt/equity."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock ticker"},
                "n_quarters": {
                    "type": "integer",
                    "description": "Number of recent quarters (default 8)",
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_earnings_data",
        "description": (
            "Pull EPS actuals vs analyst consensus estimates from IBES. "
            "Returns per-quarter: actual EPS, consensus mean/median, "
            "surprise, SUE, number of analysts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock ticker"},
                "n_quarters": {
                    "type": "integer",
                    "description": "Number of recent quarters (default 8)",
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_sector_peers",
        "description": (
            "Find same-sector peer companies and return a comparison "
            "table with key metrics (market cap, P/E, margins, EPS surprise)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Reference ticker"},
                "n_peers": {
                    "type": "integer",
                    "description": "Max peers to return (default 5)",
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_earnings_transcript",
        "description": (
            "Pull the most recent earnings call transcript from Capital IQ. "
            "Returns transcript text, date, fiscal quarter, and word count."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock ticker"},
                "quarter": {
                    "type": "string",
                    "description": "Fiscal quarter e.g. '2024Q3'. If omitted, pulls latest.",
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "analyze_text_sentiment",
        "description": (
            "Analyse the sentiment of earnings call transcript text using AI. "
            "Returns: overall sentiment, confidence, key themes, management tone, "
            "forward guidance summary, risks mentioned, notable quotes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Transcript text to analyse",
                },
                "context": {
                    "type": "string",
                    "description": "Context, e.g. 'AAPL Q3 2024 earnings call'",
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "calculate_quant_signals",
        "description": (
            "Compute quantitative signals from data already gathered: "
            "momentum (1m/3m/6m/12m), volatility, SUE, earnings momentum, "
            "profitability score, revision signal. Pass in the raw data "
            "dicts returned by other tools."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker for labelling",
                },
                "price_data": {
                    "type": "object",
                    "description": "Output from get_price_data",
                },
                "fundamentals": {
                    "type": "object",
                    "description": "Output from get_fundamentals (optional)",
                },
                "earnings_data": {
                    "type": "object",
                    "description": "Output from get_earnings_data (optional)",
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "query_research_memory",
        "description": (
            "Check persistent memory for prior research on this ticker "
            "or same-sector tickers. Call this FIRST before pulling new data "
            "to avoid redundant work. Returns prior findings, signals, "
            "and recommendations."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker to look up",
                },
                "sector": {
                    "type": "string",
                    "description": "Sector to find related research",
                },
                "n_results": {
                    "type": "integer",
                    "description": "Max results (default 5)",
                },
            },
        },
    },
    {
        "name": "save_research_memory",
        "description": (
            "Store completed research findings to persistent memory. "
            "Call this after your analysis is complete but before writing "
            "the final report. Overwrites prior entry for same ticker."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "sector": {"type": "string"},
                "recommendation": {
                    "type": "string",
                    "enum": ["buy", "sell", "hold"],
                },
                "confidence": {
                    "type": "number",
                    "description": "0.0 to 1.0",
                },
                "key_findings": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "signals": {
                    "type": "object",
                    "description": "Snapshot of computed signals",
                },
                "report_summary": {
                    "type": "string",
                    "description": "One-paragraph summary",
                },
            },
            "required": [
                "ticker",
                "sector",
                "recommendation",
                "confidence",
                "key_findings",
                "report_summary",
            ],
        },
    },
]

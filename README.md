# FinAgent — Autonomous Equity Research Agent

An LLM-driven equity research agent that uses Claude's `tool_use` API to autonomously plan and execute financial analysis. Given a research query, the agent decides which data to pull, what analysis to run, and when it has enough evidence to write a final report — with **no hardcoded control flow**.

This project demonstrates genuine agentic behavior: adaptive tool selection based on sector context, persistent memory across research sessions, and provably different execution paths for different tickers.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  User Query: "Analyse AAPL's earnings and outlook"                   │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     AGENT LOOP (agent/loop.py)                       │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Step 0: Output research plan (which tools to use & skip)     │  │
│  └────────────────────────────┬───────────────────────────────────┘  │
│                               │                                      │
│  ┌────────────────────────────▼───────────────────────────────────┐  │
│  │  Claude API call (tool_use mode)                               │  │
│  │  Input: system prompt + conversation history + 9 tool schemas  │  │
│  │  Output: tool_use blocks OR final text report                  │  │
│  └────────────────────────────┬───────────────────────────────────┘  │
│                               │                                      │
│                    ┌──────────┴──────────┐                           │
│                    │                     │                            │
│              tool_use?              text only?                       │
│                    │                     │                            │
│                    ▼                     ▼                            │
│            ┌──────────────┐     ┌────────────────┐                  │
│            │  dispatch()  │     │  FINAL REPORT  │                  │
│            │  execute tool│     │  exit loop     │                  │
│            │  append result│    └────────────────┘                  │
│            └──────┬───────┘                                         │
│                   │                                                  │
│                   └──── next iteration ─────┘                       │
│                                                                      │
│  Safety: MAX_ITERATIONS limit → forced report synthesis              │
└──────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌──────────────────────────┐
              │   9 Available Tools      │
              ├──────────────────────────┤
              │ get_price_data     (CRSP)│
              │ get_fundamentals  (Comp) │
              │ get_earnings_data (IBES) │
              │ get_sector_peers  (Comp) │
              │ get_earnings_transcript  │
              │ analyze_text_sentiment   │
              │ calculate_quant_signals  │
              │ query_research_memory    │
              │ save_research_memory     │
              └──────────────────────────┘
```

### Project Structure

```
agentic_research_agent/
├── main.py                       # CLI entry point
├── config.py                     # Settings from env vars
├── requirements.txt
├── .env.example
│
├── agent/                        # Core orchestration (70% of value)
│   ├── loop.py                   # ReAct agent loop
│   ├── prompts.py                # System prompt + tool schemas
│   └── models.py                 # AgentState, ToolResult, EvalRecord
│
├── tools/                        # 9 callable tools
│   ├── registry.py               # Name → function dispatch
│   ├── price_data.py             # CRSP daily prices/returns
│   ├── fundamentals.py           # Compustat quarterly fundamentals
│   ├── earnings_data.py          # IBES actuals vs estimates
│   ├── sector_peers.py           # Same-SIC peer comparison
│   ├── earnings_transcript.py    # Capital IQ transcript text
│   ├── sentiment.py              # Claude-based transcript analysis
│   ├── quant_signals.py          # Momentum, SUE, profitability
│   ├── memory_query.py           # Read persistent memory
│   └── memory_save.py            # Write persistent memory
│
├── data/                         # Data access layer
│   ├── wrds_client.py            # Live WRDS (all SQL in one file)
│   └── mock_client.py            # Bundled fixtures (same interface)
│
├── memory/
│   └── store.py                  # JSON store at ~/.finagent/
│
├── mock_data/                    # Sample data for 5 tickers
│   ├── price_data.json           # 2 years daily prices
│   ├── fundamentals.json         # 8 quarters per ticker
│   ├── earnings_data.json        # IBES actuals + estimates
│   ├── transcripts.json          # Earnings call excerpts
│   ├── company_info.json         # SIC codes
│   └── sector_peers.json         # Peer companies
│
└── evaluation/
    ├── runner.py                 # Batch eval across tickers
    └── metrics.py                # Path diversity, token stats
```

## Setup

### Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)
- (Optional) [WRDS](https://wrds-www.wharton.upenn.edu/) institutional subscription for live data

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/agentic-research-agent.git
cd agentic-research-agent
pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
# Edit .env:
#   ANTHROPIC_API_KEY=sk-ant-...    (required)
#   WRDS_USERNAME=your_username      (required for live mode only)
```

### Mock Mode (no WRDS needed)

Bundled sample data covers 5 tickers across 4 sectors: AAPL (Tech), JPM (Financials), JNJ (Healthcare), XOM (Energy), WMT (Consumer Staples).

```bash
python main.py "Analyse AAPL's recent earnings and outlook"
```

### Live Mode (real WRDS data)

Requires a WRDS institutional subscription with access to CRSP, Compustat, IBES, and Capital IQ.

```bash
python main.py --live "Analyse AAPL's recent earnings and outlook"
```

### WRDS Data License

This project queries WRDS (Wharton Research Data Services) databases: CRSP, Compustat, IBES, and Capital IQ. These are proprietary datasets subject to institutional licensing. **No WRDS data is committed to this repository.** The mock data contains synthetic fixtures only. You must have your own WRDS subscription to use live mode.

## Usage

```bash
# Single research query
python main.py "Analyse JPM: credit quality and earnings trends"

# Live WRDS mode
python main.py --live "Analyse XOM's production trends and valuation"

# Full evaluation suite
python main.py --evaluate                  # mock mode
python main.py --evaluate --live           # live WRDS mode
python main.py --evaluate --ticker AAPL    # single ticker

# Verbose logging
python main.py -v "Analyse WMT"
```

## Evaluation Results (Live WRDS Data)

Evaluated on 5 tickers across different sectors, plus a repeat test for memory-aware behavior:

| Ticker | Sector | Steps | Tools | Tokens | Latency | Rec | Confidence |
|--------|--------|-------|-------|--------|---------|-----|------------|
| AAPL | Technology | 7 | 6 | 49,786 | 67s | BUY | 85% |
| JPM | Financials | 8 | 7 | 54,862 | 256s | HOLD | 75% |
| JNJ | Healthcare | 7 | 6 | 53,408 | 75s | BUY | 85% |
| XOM | Energy | 7 | 6 | 43,379 | 63s | HOLD | 72% |
| WMT | Consumer Staples | 7 | 6 | 40,987 | 71s | BUY | 85% |

**Averages:** 7.2 steps, 48,484 tokens, 106s per research run.

### Adaptive Planning: 100% Path Diversity

All 5 tickers produced **unique tool sequences** — the agent genuinely adapts its analysis path based on sector and intermediate findings:

| Ticker | Tool Sequence |
|--------|---------------|
| **AAPL** (Tech) | memory → price → earnings → fundamentals → quant signals → save |
| **JPM** (Bank) | memory → fundamentals → earnings → price → **sector peers** → quant signals → save |
| **JNJ** (Pharma) | memory → fundamentals → earnings → **transcript → sentiment** → save |
| **XOM** (Energy) | memory → fundamentals → earnings → price → quant signals → save |
| **WMT** (Retail) | memory → fundamentals → earnings → **peers → transcript** → save |

Key observations:
- **JNJ** was the only ticker where the agent pulled a transcript and ran sentiment analysis — pharma pipeline updates are critical for investment thesis
- **JPM** was one of two tickers where the agent pulled sector peers — bank peer comparison is meaningful
- **AAPL/XOM** focused on quantitative signals and skipped qualitative analysis
- `analyze_text_sentiment` was called only **1 time** across 5 runs (vs. 5/5 before the fix)

### Memory Test: Repeat Run Comparison

Running AAPL twice proves persistent memory changes the agent's behavior:

| | First Run | Second Run (with memory) | Delta |
|--|-----------|--------------------------|-------|
| **Steps** | 7 | 6 | -1 |
| **Tool calls** | 6 | 5 | -1 |
| **Tokens** | 49,786 | 36,567 | **-27%** |
| **Latency** | 67s | 67s | — |
| **Confidence** | 85% | 80% | -5% |

**Tools skipped in second run:** `get_fundamentals` — the agent found prior fundamentals in memory and decided they were still current.

**Second run tool sequence:**
```
query_research_memory → get_price_data → get_earnings_data → calculate_quant_signals → save_research_memory
```

The agent pulled only time-sensitive data (prices, latest earnings) and skipped static data (fundamentals), using 27% fewer tokens.

## Design Decisions

1. **Report as exit condition.** The final report is not a tool — it's Claude's natural text response when it decides it has enough data. No tool call = loop exits.

2. **Mandatory research plan.** Before any data pull, the agent outputs a text plan stating which tools to use and which to skip. This forces genuine planning rather than reflexive tool-calling.

3. **Sector-aware prompting.** The system prompt includes sector-specific guidance (e.g., "for pharma, prioritise transcripts for pipeline updates; for energy, skip peer comparison"). This drives the path diversity.

4. **Single data layer.** All WRDS SQL lives in `data/wrds_client.py`. `mock_client.py` implements the same interface. One config toggle switches modes.

5. **Claude for sentiment.** Transcript analysis uses Claude (not FinBERT), enabling nuanced qualitative judgment with structured JSON output.

6. **Max iteration safety.** Configurable `MAX_ITERATIONS` (default 15). If reached, Claude is forced to synthesise a report from whatever it has.

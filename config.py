"""
Central configuration for FinAgent.

All tunables live here. Credentials come from environment variables.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from this project's root directory (next to config.py)
_project_env = Path(__file__).resolve().parent / ".env"
load_dotenv(_project_env)

# Also load .env from parent directory (earnings_text_alpha root)
_parent_env = Path(__file__).resolve().parent.parent / ".env"
if _parent_env.exists():
    load_dotenv(_parent_env)

# --- Credentials (never hardcoded) ---
WRDS_USERNAME: str = os.environ.get("WRDS_USERNAME", "")
ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")

# --- Agent loop ---
MAX_ITERATIONS: int = 15
AGENT_MODEL: str = "claude-sonnet-4-20250514"
SENTIMENT_MODEL: str = "claude-haiku-4-5-20251001"
MAX_TOKENS: int = 4096

# --- Data ---
DATA_MODE: str = "mock"  # "live" or "mock"
DEFAULT_START_DATE: str = "2023-01-01"
DEFAULT_END_DATE: str = "2024-12-31"
DEFAULT_N_QUARTERS: int = 8

# --- Paths ---
ROOT: Path = Path(__file__).resolve().parent
MOCK_DATA_DIR: Path = ROOT / "mock_data"
OUTPUT_DIR: Path = ROOT / "output"
MEMORY_PATH: Path = Path.home() / ".finagent" / "research_memory.json"

for _d in (OUTPUT_DIR, MEMORY_PATH.parent):
    _d.mkdir(parents=True, exist_ok=True)

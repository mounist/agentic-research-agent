"""
Live WRDS data client. All SQL lives here.

Manages a singleton wrds.Connection. Provides typed query methods
that tool modules call.
"""
from __future__ import annotations

import logging
from typing import Any

import pandas as pd

import config

logger = logging.getLogger(__name__)

_conn = None


def _get_conn():
    """Lazy-init a WRDS connection."""
    global _conn
    if _conn is None:
        import wrds
        _conn = wrds.Connection(wrds_username=config.WRDS_USERNAME)
        logger.info("WRDS connection established.")
    return _conn


def close() -> None:
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None


# ── Ticker resolution ─────────────────────────────────────────────────

def resolve_ticker_to_permno(ticker: str) -> int | None:
    """CRSP ticker → permno."""
    db = _get_conn()
    df = db.raw_sql(
        "SELECT DISTINCT permno FROM crsp.dsenames "
        "WHERE ticker = %(ticker)s AND namedt <= CURRENT_DATE AND "
        "(nameendt >= CURRENT_DATE OR nameendt IS NULL) "
        "ORDER BY permno LIMIT 1",
        params={"ticker": ticker.upper()},
    )
    return int(df.iloc[0]["permno"]) if len(df) > 0 else None


def resolve_ticker_to_gvkey(ticker: str) -> str | None:
    """Compustat ticker → gvkey."""
    db = _get_conn()
    df = db.raw_sql(
        "SELECT DISTINCT gvkey FROM comp.security "
        "WHERE tic = %(ticker)s LIMIT 1",
        params={"ticker": ticker.upper()},
    )
    return str(df.iloc[0]["gvkey"]) if len(df) > 0 else None


# ── CRSP ──────────────────────────────────────────────────────────────

def query_crsp_daily(
    ticker: str,
    start_date: str = config.DEFAULT_START_DATE,
    end_date: str = config.DEFAULT_END_DATE,
) -> pd.DataFrame:
    """Daily stock data from CRSP."""
    db = _get_conn()
    return db.raw_sql(
        """
        SELECT a.date, a.prc, a.ret, a.vol, a.shrout
        FROM crsp.dsf a
        JOIN crsp.dsenames b ON a.permno = b.permno
        WHERE b.ticker = %(ticker)s
          AND a.date BETWEEN %(start)s AND %(end)s
          AND b.namedt <= a.date
          AND (b.nameendt >= a.date OR b.nameendt IS NULL)
        ORDER BY a.date
        """,
        params={"ticker": ticker.upper(), "start": start_date, "end": end_date},
    )


# ── Compustat ─────────────────────────────────────────────────────────

def query_compustat_fundq(ticker: str, n_quarters: int = 8) -> pd.DataFrame:
    """Quarterly fundamentals from Compustat."""
    db = _get_conn()
    return db.raw_sql(
        """
        SELECT a.datadate, a.fyearq, a.fqtr, a.revtq, a.niq,
               a.epspxq, a.epsfxq, a.atq, a.ltq, a.ceqq,
               a.oiadpq, (a.saleq - a.cogsq) AS gpq,
               a.cshoq, a.prccq, a.saleq
        FROM comp.fundq a
        JOIN comp.security b ON a.gvkey = b.gvkey
        WHERE b.tic = %(ticker)s
          AND a.datafmt = 'STD' AND a.indfmt = 'INDL'
          AND a.consol = 'C' AND a.popsrc = 'D'
        ORDER BY a.datadate DESC
        LIMIT %(n)s
        """,
        params={"ticker": ticker.upper(), "n": n_quarters},
    )


def query_compustat_company(ticker: str) -> pd.DataFrame:
    """Company info for SIC code lookup."""
    db = _get_conn()
    return db.raw_sql(
        "SELECT gvkey, conm, sic, naics FROM comp.company "
        "WHERE gvkey IN (SELECT gvkey FROM comp.security WHERE tic = %(ticker)s)",
        params={"ticker": ticker.upper()},
    )


def query_sector_peers(
    sic2: str, exclude_gvkey: str, n: int = 5
) -> pd.DataFrame:
    """Find peers by 2-digit SIC code with recent fundamentals."""
    db = _get_conn()
    return db.raw_sql(
        """
        SELECT c.gvkey, c.conm, s.tic,
               f.revtq, f.niq, f.epspxq, f.prccq, f.cshoq
        FROM comp.company c
        JOIN comp.security s ON c.gvkey = s.gvkey
        JOIN comp.fundq f ON c.gvkey = f.gvkey
        WHERE SUBSTRING(c.sic, 1, 2) = %(sic2)s
          AND c.gvkey != %(exclude)s
          AND f.datadate = (
              SELECT MAX(f2.datadate) FROM comp.fundq f2
              WHERE f2.gvkey = c.gvkey AND f2.datafmt = 'STD'
          )
          AND f.datafmt = 'STD' AND f.indfmt = 'INDL'
        ORDER BY f.prccq * f.cshoq DESC NULLS LAST
        LIMIT %(n)s
        """,
        params={"sic2": sic2, "exclude": exclude_gvkey, "n": n},
    )


# ── IBES ──────────────────────────────────────────────────────────────

def query_ibes_actuals(ticker: str, n_quarters: int = 8) -> pd.DataFrame:
    """EPS actuals from IBES."""
    db = _get_conn()
    return db.raw_sql(
        """
        SELECT ticker, pends, anndats, value AS actual_eps, measure
        FROM ibes.actu_epsus
        WHERE ticker = %(ticker)s AND measure = 'EPS'
        ORDER BY pends DESC
        LIMIT %(n)s
        """,
        params={"ticker": ticker.upper(), "n": n_quarters},
    )


def query_ibes_estimates(ticker: str, n_quarters: int = 8) -> pd.DataFrame:
    """Summary statistics of analyst estimates joined with actuals from IBES."""
    db = _get_conn()
    return db.raw_sql(
        """
        SELECT DISTINCT ON (s.fpedats)
               s.ticker, s.fpedats, s.statpers, s.meanest, s.medest,
               s.stdev, s.numest, a.value AS actual
        FROM ibes.statsumu_epsus s
        LEFT JOIN (
            SELECT ticker, pends, value
            FROM ibes.actu_epsus
            WHERE measure = 'EPS' AND pdicity = 'QTR'
        ) a ON s.ticker = a.ticker AND s.fpedats = a.pends
        WHERE s.ticker = %(ticker)s
          AND s.measure = 'EPS' AND s.fpi = '6'
          AND s.statpers = (
              SELECT MAX(s2.statpers) FROM ibes.statsumu_epsus s2
              WHERE s2.ticker = s.ticker AND s2.fpedats = s.fpedats
                AND s2.measure = 'EPS' AND s2.fpi = '6'
          )
        ORDER BY s.fpedats DESC, a.value
        LIMIT %(n)s
        """,
        params={"ticker": ticker.upper(), "n": n_quarters},
    )


# ── Capital IQ transcripts ───────────────────────────────────────────

def query_ciq_transcript(ticker: str, quarter: str | None = None) -> pd.DataFrame:
    """Earnings call transcript from CIQ.

    Uses ciqtranscriptcomponent (text) joined to wrds_transcript_detail
    (metadata with companyid/date) and ciq.wrds_gvkey (ticker mapping).
    """
    db = _get_conn()
    params: dict[str, Any] = {"ticker": ticker.upper()}

    # First find the most recent transcriptid for this ticker
    tid_df = db.raw_sql(
        """
        SELECT td.transcriptid, td.mostimportantdateutc AS transcriptdate,
               td.headline
        FROM ciq.wrds_transcript_detail td
        JOIN ciq.wrds_gvkey g ON td.companyid = g.companyid
        JOIN comp.security s ON g.gvkey = s.gvkey
        WHERE s.tic = %(ticker)s
          AND td.keydeveventtypename = 'Earnings Calls'
        ORDER BY td.mostimportantdateutc DESC
        LIMIT 1
        """,
        params=params,
    )
    if tid_df.empty:
        return pd.DataFrame()

    transcript_id = int(tid_df.iloc[0]["transcriptid"])
    transcript_date = str(tid_df.iloc[0]["transcriptdate"])

    # Now pull the component text for that transcript
    comp_df = db.raw_sql(
        """
        SELECT componentorder, componenttext
        FROM ciq.ciqtranscriptcomponent
        WHERE transcriptid = %(tid)s
        ORDER BY componentorder
        """,
        params={"tid": transcript_id},
    )

    if comp_df.empty:
        return pd.DataFrame()

    # Return as single row with concatenated text
    full_text = "\n\n".join(comp_df["componenttext"].dropna().astype(str).tolist())
    return pd.DataFrame([{
        "transcriptid": transcript_id,
        "transcriptdate": transcript_date,
        "componenttext": full_text,
    }])


def query_all_transcripts(ticker: str, n_quarters: int = 8) -> list[dict[str, Any]]:
    """Return recent earnings-call transcripts for ``ticker`` (RAG indexing).

    Each dict carries ``ticker``, ``quarter``, ``transcriptdate`` and
    ``componenttext`` (full concatenated transcript body). Ordered oldest
    to newest so downstream chunk IDs are stable across incremental runs.
    """
    db = _get_conn()
    tid_df = db.raw_sql(
        """
        SELECT td.transcriptid, td.mostimportantdateutc AS transcriptdate,
               td.headline
        FROM ciq.wrds_transcript_detail td
        JOIN ciq.wrds_gvkey g ON td.companyid = g.companyid
        JOIN comp.security s ON g.gvkey = s.gvkey
        WHERE s.tic = %(ticker)s
          AND td.keydeveventtypename = 'Earnings Calls'
        ORDER BY td.mostimportantdateutc DESC
        LIMIT %(n)s
        """,
        params={"ticker": ticker.upper(), "n": int(n_quarters)},
    )
    if tid_df.empty:
        return []

    # Keep only the latest transcript per quarter to avoid duplicate chunk IDs
    # downstream (rescheduled / amended calls can share a quarter bucket).
    tid_df = tid_df.drop_duplicates(subset=["transcriptid"])
    tid_df = tid_df.sort_values("transcriptdate")
    tid_df["_quarter"] = tid_df["transcriptdate"].apply(
        lambda d: (lambda t: f"{t.year}Q{((t.month - 1) // 3) + 1}")(pd.Timestamp(d))
    )
    tid_df = tid_df.drop_duplicates(subset=["_quarter"], keep="last")

    records: list[dict[str, Any]] = []
    for _, row in tid_df.iterrows():
        tid = int(row["transcriptid"])
        comp_df = db.raw_sql(
            "SELECT componentorder, componenttext FROM ciq.ciqtranscriptcomponent "
            "WHERE transcriptid = %(tid)s ORDER BY componentorder",
            params={"tid": tid},
        )
        if comp_df.empty:
            continue
        full_text = "\n\n".join(comp_df["componenttext"].dropna().astype(str).tolist())
        tdate = pd.Timestamp(row["transcriptdate"])
        quarter = f"{tdate.year}Q{((tdate.month - 1) // 3) + 1}"
        records.append({
            "ticker": ticker.upper(),
            "quarter": quarter,
            "transcriptdate": str(row["transcriptdate"]),
            "transcriptid": tid,
            "componenttext": full_text,
            "text": full_text,
        })
    return records

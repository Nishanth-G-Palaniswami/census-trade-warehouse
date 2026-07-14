"""Ingestion: pull one month of Census imports (live if CENSUS_API_KEY is set,
otherwise the bundled offline sample) and land it into DuckDB as raw.imports.

Runnable standalone so the warehouse can be built without Dagster:

    python -m census_trade.ingest --period 2023-12
"""

from __future__ import annotations

import argparse
import csv
from importlib.resources import files
from pathlib import Path

import duckdb

from .census_api import CensusClient
from .config import DEFAULT_PERIOD, DUCKDB_PATH, RAW_SCHEMA, RAW_TABLE, ensure_data_dir

SAMPLE_CSV = files("census_trade").joinpath("data/sample_imports.csv")

COLUMNS = ["period", "cty_code", "cty_name", "hs2", "gen_val_mo"]


def load_sample(period: str) -> list[dict]:
    """Read the committed offline sample, re-stamped to `period`."""
    text = SAMPLE_CSV.read_text(encoding="utf-8")
    rows = list(csv.DictReader(text.splitlines()))
    out = []
    for r in rows:
        out.append(
            {
                "period": period,
                "cty_code": r["cty_code"],
                "cty_name": r["cty_name"],
                "hs2": r["hs2"],
                "gen_val_mo": int(r["gen_val_mo"]),
            }
        )
    return out


def get_rows(period: str) -> tuple[list[dict], str]:
    """Return (rows, source) — live Census data if a key is present, else the
    offline sample. The source string is surfaced as asset metadata."""
    client = CensusClient.from_env()
    if client.has_key:
        return client.fetch(period), "census_api"
    return load_sample(period), "offline_sample"


def land(rows: list[dict], duckdb_path: Path = DUCKDB_PATH) -> int:
    """(Re)create raw.imports for the row set's period(s) and insert. Idempotent
    per period: an existing period is deleted before insert so re-runs don't
    duplicate."""
    ensure_data_dir()
    con = duckdb.connect(str(duckdb_path))
    try:
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {RAW_SCHEMA}")
        con.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {RAW_SCHEMA}.{RAW_TABLE} (
                period      VARCHAR,
                cty_code    VARCHAR,
                cty_name    VARCHAR,
                hs2         VARCHAR,
                gen_val_mo  BIGINT,
                _ingested_at TIMESTAMP DEFAULT now()
            )
            """
        )
        periods = sorted({r["period"] for r in rows})
        for p in periods:
            con.execute(
                f"DELETE FROM {RAW_SCHEMA}.{RAW_TABLE} WHERE period = ?", [p]
            )
        con.executemany(
            f"INSERT INTO {RAW_SCHEMA}.{RAW_TABLE} "
            f"(period, cty_code, cty_name, hs2, gen_val_mo) VALUES (?, ?, ?, ?, ?)",
            [[r[c] for c in COLUMNS] for r in rows],
        )
        return len(rows)
    finally:
        con.close()


def run(period: str = DEFAULT_PERIOD) -> dict:
    rows, source = get_rows(period)
    n = land(rows)
    return {"period": period, "rows": n, "source": source, "duckdb": str(DUCKDB_PATH)}


def main() -> None:
    ap = argparse.ArgumentParser(description="Land Census imports into DuckDB.")
    ap.add_argument("--period", default=DEFAULT_PERIOD, help="YYYY-MM")
    args = ap.parse_args()
    result = run(args.period)
    print(
        f"landed {result['rows']} rows for {result['period']} "
        f"({result['source']}) -> {result['duckdb']}"
    )


if __name__ == "__main__":
    main()

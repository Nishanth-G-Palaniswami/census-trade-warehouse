"""Shared configuration — resolved once so dbt and the ingestion layer agree
on a single, absolute DuckDB path regardless of the working directory dbt or
Dagster happens to run from."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Importing this module sets CENSUS_DUCKDB if it isn't already set, so a dbt run
# launched by Dagster (cwd = the dbt project dir) reads `env_var('CENSUS_DUCKDB')`
# and lands in the same absolute file the ingestion asset wrote to.
DUCKDB_PATH = Path(
    os.environ.setdefault(
        "CENSUS_DUCKDB", str(REPO_ROOT / "data" / "warehouse.duckdb")
    )
)

# raw landing target
RAW_SCHEMA = "raw"
RAW_TABLE = "imports"

# Default period to ingest when none is given (a fixed, always-available month —
# override with --period YYYY-MM or the CENSUS_PERIOD env var).
DEFAULT_PERIOD = os.environ.get("CENSUS_PERIOD", "2023-12")


def ensure_data_dir() -> None:
    DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)

"""Dagster <-> dbt project handle. Importing this also resolves the shared
DuckDB path (via config) so dbt, launched with cwd = the dbt project dir, reads
the same absolute CENSUS_DUCKDB the ingestion asset wrote to."""

from __future__ import annotations

from pathlib import Path

from dagster_dbt import DbtProject

from . import config  # noqa: F401 — side effect: sets CENSUS_DUCKDB

dbt_project = DbtProject(
    project_dir=Path(__file__).joinpath("..", "..", "census_dbt").resolve(),
)
dbt_project.prepare_if_dev()

# `@dbt_assets` reads the manifest at import time. Under `dagster dev`,
# prepare_if_dev() builds it; everywhere else (pytest, CI, `dagster definitions
# validate`, or `python -m census_trade.ingest`, all of which import this
# package) we build it on demand so the project works straight from a clone.
if not dbt_project.manifest_path.exists():
    from dbt.cli.main import dbtRunner

    dbtRunner().invoke(
        [
            "parse",
            "--project-dir",
            str(dbt_project.project_dir),
            "--profiles-dir",
            str(dbt_project.project_dir),
        ]
    )

"""Dagster assets: one Python asset ingests raw Census data into DuckDB; the dbt
models are loaded as downstream assets. The dbt source `census_raw.imports` is
mapped (via meta.dagster.asset_key in _sources.yml) to the same asset key the
ingestion produces, so Dagster knows dbt runs *after* ingestion.

NOTE: no `from __future__ import annotations` here — Dagster inspects the real
`context`/resource annotations at runtime, and PEP 563 stringized hints break
that validation."""

from dagster import AssetExecutionContext, Config, MaterializeResult, MetadataValue, asset
from dagster_dbt import DbtCliResource, dbt_assets

from . import ingest
from .config import DEFAULT_PERIOD, RAW_SCHEMA, RAW_TABLE
from .project import dbt_project

RAW_ASSET_KEY = [RAW_SCHEMA, RAW_TABLE]  # ["raw", "imports"]


class IngestConfig(Config):
    """Which reporting month to land. Manual runs default to a fixed,
    always-available month (reproducible); the monthly schedule overrides this
    with the latest published period computed from the tick date."""

    period: str = DEFAULT_PERIOD


@asset(key=RAW_ASSET_KEY, compute_kind="python", group_name="ingestion")
def raw_imports(context: AssetExecutionContext, config: IngestConfig) -> MaterializeResult:
    """Pull one month of U.S. imports (live Census API if CENSUS_API_KEY is set,
    otherwise the bundled offline sample) and land it into raw.imports."""
    result = ingest.run(config.period)
    context.log.info(
        f"Landed {result['rows']} rows for {result['period']} "
        f"from {result['source']}."
    )
    return MaterializeResult(
        metadata={
            "rows": MetadataValue.int(result["rows"]),
            "period": MetadataValue.text(result["period"]),
            "source": MetadataValue.text(result["source"]),
            "duckdb_path": MetadataValue.path(result["duckdb"]),
        }
    )


@dbt_assets(manifest=dbt_project.manifest_path)
def census_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    """staging + marts, built and tested via `dbt build`."""
    yield from dbt.cli(["build"], context=context).stream()

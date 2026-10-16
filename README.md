# Census Trade Warehouse

[![ci](https://github.com/Nishanth-G-Palaniswami/census-trade-warehouse/actions/workflows/ci.yml/badge.svg)](https://github.com/Nishanth-G-Palaniswami/census-trade-warehouse/actions/workflows/ci.yml)

An orchestrated ELT pipeline that turns monthly **U.S. Census Bureau international-trade data** into a queryable **DuckDB** warehouse, transformed and tested with **dbt** and orchestrated with **Dagster**.

Runs end-to-end on a laptop, with no cloud account and **no API key required**: a small offline sample is bundled so `dagster dev` and CI work immediately; add a free Census key for live data.

```
Census API ─▶ raw.imports (DuckDB)  ─▶  dbt staging  ─▶  dbt marts
  (Dagster asset: ingest)               (typed/clean)     (top partners,
                                                            imports by HS chapter)
        └──────────────── Dagster orchestrates + schedules monthly ───────────────┘
```

## Why this design

- **Orchestrated, not a notebook.** Census releases trade data monthly, so the pipeline is scheduled (`monthly_refresh`, the 10th at 6am ET) and each stage is an addressable Dagster asset with lineage and run history. That is the difference between a one-off script and something you can operate.
- **ELT with dbt on DuckDB.** Raw data lands first, then dbt transforms it in-warehouse: a typed `staging` view and two `marts` (top trading partners; imports by HS2 product chapter with share-of-total). DuckDB keeps it single-file and zero-infra.
- **Tested.** dbt data tests (`not_null` on keys, two singular tests: non-negative values, mart grain uniqueness) plus Python unit tests for the API client. CI runs the whole thing on the offline sample.
- **Reproducible offline.** The ingestion asset falls back to a committed sample when `CENSUS_API_KEY` is unset, so the repo clones-and-runs and CI needs no secret.

## Stack

Dagster · dagster-dbt · dbt-duckdb · DuckDB · Python (stdlib `urllib` for the API client) · pytest · GitHub Actions

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Absolute warehouse path shared by ingestion + dbt:
export CENSUS_DUCKDB="$PWD/data/warehouse.duckdb"       # Windows PS: $env:CENSUS_DUCKDB="$PWD\data\warehouse.duckdb"

# Run the whole pipeline in the Dagster UI (uses the offline sample):
dagster dev
# then open http://localhost:3000 and click "Materialize all"
```

### Live data (optional)

```bash
cp .env.example .env      # add your free key from api.census.gov/data/key_signup.html
export CENSUS_API_KEY=...  # or put it in .env
# ingestion now pulls live Census data instead of the sample
```

### Run without Dagster (just the warehouse)

```bash
export CENSUS_DUCKDB="$PWD/data/warehouse.duckdb"
python -m census_trade.ingest --period 2023-12   # land raw.imports
cd census_dbt && dbt build --profiles-dir .       # build + test staging + marts
```

Then query it:

```bash
duckdb "$CENSUS_DUCKDB" "select country_name, total_import_value_usd, partner_rank
                         from main_marts.mart_top_partners order by partner_rank limit 10"
```

## Layout

```
census_trade/            # Dagster code location
  census_api.py          # Census client: pure build_query / parse_response + fetch
  ingest.py              # land raw.imports (live key or offline sample); runnable standalone
  assets.py              # raw_imports asset + dbt models as downstream assets
  schedules.py           # monthly refresh schedule
  config.py              # single source of the absolute DuckDB path
  data/sample_imports.csv# offline sample (25 rows, Dec 2023, 5 partners x 5 HS2)
census_dbt/              # dbt project
  models/staging/        # stg_imports (+ source mapped to the Dagster asset key)
  models/marts/          # mart_top_partners, mart_imports_by_hs2
  tests/                 # singular data tests
tests/                   # pytest: offline unit tests for the API client
.github/workflows/ci.yml # pytest -> ingest (sample) -> dbt build -> dagster validate
```

## Data source

U.S. Census Bureau, International Trade API: `timeseries/intltrade/imports/hs`. Public government data; this project is independent of any employer work.

## License

MIT, see [LICENSE](LICENSE).

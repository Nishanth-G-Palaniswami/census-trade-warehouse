"""Dagster code location for the Census trade warehouse."""

from __future__ import annotations

from dagster import Definitions
from dagster_dbt import DbtCliResource

from .assets import census_dbt_assets, raw_imports
from .project import dbt_project
from .schedules import schedules

defs = Definitions(
    assets=[raw_imports, census_dbt_assets],
    resources={"dbt": DbtCliResource(project_dir=dbt_project)},
    schedules=schedules,
)

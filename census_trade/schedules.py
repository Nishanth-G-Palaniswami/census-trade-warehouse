"""A monthly schedule that rebuilds the whole warehouse — Census import data is
released monthly, which is exactly what makes an orchestrated pipeline (rather
than a one-off notebook) the right tool here."""

from __future__ import annotations

from dagster import AssetSelection, ScheduleDefinition, define_asset_job

rebuild_warehouse_job = define_asset_job(
    name="rebuild_warehouse",
    selection=AssetSelection.all(),
)

# 6:00 AM on the 10th of each month — after Census' typical monthly release.
monthly_refresh = ScheduleDefinition(
    name="monthly_refresh",
    job=rebuild_warehouse_job,
    cron_schedule="0 6 10 * *",
    execution_timezone="America/New_York",
)

schedules = [monthly_refresh]

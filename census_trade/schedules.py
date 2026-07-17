"""A monthly schedule that rebuilds the whole warehouse — Census import data is
released monthly, which is exactly what makes an orchestrated pipeline (rather
than a one-off notebook) the right tool here.

The schedule computes the newest published reporting month from its own tick
date (Census publishes with a ~2-month lag) and passes it to the ingestion
asset as run config, so each monthly run ingests fresh data instead of
re-landing the manual-run default period.
"""

from __future__ import annotations

from dagster import AssetSelection, RunRequest, define_asset_job, schedule

from .period import latest_published_period

rebuild_warehouse_job = define_asset_job(
    name="rebuild_warehouse",
    selection=AssetSelection.all(),
)


# 6:00 AM on the 10th of each month — after Census' typical monthly release.
@schedule(
    job=rebuild_warehouse_job,
    cron_schedule="0 6 10 * *",
    execution_timezone="America/New_York",
)
def monthly_refresh(context):
    period = latest_published_period(context.scheduled_execution_time.date())
    return RunRequest(
        run_key=period,  # one run per period — reruns of the same tick dedupe
        run_config={"ops": {"raw_imports": {"config": {"period": period}}}},
    )


schedules = [monthly_refresh]

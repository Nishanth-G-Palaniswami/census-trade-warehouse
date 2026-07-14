-- Import value by HS2 product chapter per period, with a share-of-total and a
-- count of contributing countries.
with imports as (
    select * from {{ ref('stg_imports') }}
),

by_chapter as (
    select
        period,
        hs2_code,
        sum(import_value_usd)        as import_value_usd,
        count(distinct country_code) as source_countries
    from imports
    group by period, hs2_code
),

period_total as (
    select period, sum(import_value_usd) as period_total_usd
    from imports
    group by period
)

select
    c.period,
    c.hs2_code,
    c.import_value_usd,
    c.source_countries,
    round(c.import_value_usd * 100.0 / t.period_total_usd, 2) as pct_of_period
from by_chapter c
join period_total t using (period)

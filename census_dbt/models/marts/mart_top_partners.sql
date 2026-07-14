-- Total U.S. import value by trading partner per period, ranked. This is the
-- "top 20 partners" view the app-layer would read.
with imports as (
    select * from {{ ref('stg_imports') }}
)

select
    period,
    country_code,
    country_name,
    sum(import_value_usd) as total_import_value_usd,
    row_number() over (
        partition by period
        order by sum(import_value_usd) desc
    ) as partner_rank
from imports
group by period, country_code, country_name

-- Total U.S. import value by trading partner per period, with a rank per
-- period. Every partner is kept; consumers filter on partner_rank (e.g.
-- partner_rank <= 20 for a "top 20" view).
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

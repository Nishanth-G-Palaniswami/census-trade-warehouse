-- Singular data test: mart_top_partners must be unique at (period, country_code).
-- Returns any grain that appears more than once.
select period, country_code, count(*) as n
from {{ ref('mart_top_partners') }}
group by period, country_code
having count(*) > 1

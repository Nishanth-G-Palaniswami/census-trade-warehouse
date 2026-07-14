-- Singular data test: import values must never be negative. Returns the
-- offending rows; dbt fails the test if any come back.
select period, country_code, hs2_code, import_value_usd
from {{ ref('stg_imports') }}
where import_value_usd < 0

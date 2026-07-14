-- Typed, cleaned view over the raw landing table: one row per
-- (period, country, HS2 chapter). Drops rows with a null value or country.
with source as (
    select * from {{ source('census_raw', 'imports') }}
)

select
    period,
    cast(cty_code as varchar)  as country_code,
    cty_name                   as country_name,
    cast(hs2 as varchar)       as hs2_code,
    cast(gen_val_mo as bigint) as import_value_usd
from source
where gen_val_mo is not null
  and cty_code   is not null

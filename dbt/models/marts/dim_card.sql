-- One row per card with simple behavioral attributes.
select
    card_id,
    min(ts)                   as first_seen_at,
    max(ts)                   as last_seen_at,
    count(*)                  as txn_count,
    avg(amount)               as avg_amount,
    count_if(country <> 'US') as foreign_txn_count
from {{ ref('stg_card_txns') }}
group by card_id

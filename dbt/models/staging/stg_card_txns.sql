-- Clean and deduplicate raw transactions.
-- Kafka is at-least-once, so the same txn_id can arrive twice: keep the first load.
with ranked as (
    select
        txn_id,
        card_id,
        merchant,
        mcc,
        amount,
        currency,
        country,
        ts,
        is_fraud,
        loaded_at,
        row_number() over (partition by txn_id order by loaded_at) as rn
    from {{ source('raw', 'CARD_TXNS') }}
    where txn_id is not null
      and amount > 0
)

select
    txn_id,
    card_id,
    merchant,
    mcc,
    amount,
    currency,
    country,
    ts,
    is_fraud,
    loaded_at
from ranked
where rn = 1

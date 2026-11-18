-- Fact table: one row per transaction, keyed to card and merchant dimensions.
select
    t.txn_id,
    t.card_id,
    {{ dbt_utils_surrogate_key_fallback(['t.merchant', 't.mcc']) }} as merchant_key,
    t.amount,
    t.currency,
    t.country,
    t.ts,
    date(t.ts) as txn_date,
    hour(t.ts) as txn_hour,
    t.is_fraud
from {{ ref('stg_card_txns') }} as t

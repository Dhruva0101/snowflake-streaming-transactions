select distinct
    {{ dbt_utils_surrogate_key_fallback(['merchant', 'mcc']) }} as merchant_key,
    merchant,
    mcc
from {{ ref('stg_card_txns') }}

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from generator.transactions import CURRENCY, generate, to_dict  # noqa: E402


def test_generates_requested_count():
    assert len(generate(250, seed=1)) == 250


def test_same_seed_is_reproducible():
    a = [to_dict(t) for t in generate(50, seed=7)]
    b = [to_dict(t) for t in generate(50, seed=7)]
    assert a == b


def test_txn_ids_are_unique():
    txns = generate(5000, seed=3)
    assert len({t.txn_id for t in txns}) == len(txns)


def test_fields_are_valid():
    for t in generate(1000, seed=11):
        assert t.amount > 0
        assert t.currency == CURRENCY[t.country]
        assert len(t.mcc) == 4 and t.mcc.isdigit()
        assert t.card_id.startswith("card_")


def test_fraud_rate_is_roughly_one_percent():
    txns = generate(20000, seed=5)
    rate = sum(t.is_fraud for t in txns) / len(txns)
    assert 0.005 < rate < 0.02


def test_fraud_skews_to_larger_amounts():
    txns = generate(20000, seed=5)
    fraud = [t.amount for t in txns if t.is_fraud]
    normal = [t.amount for t in txns if not t.is_fraud]
    assert sum(fraud) / len(fraud) > sum(normal) / len(normal)


def test_records_are_json_serializable():
    for t in generate(10, seed=2):
        json.dumps(to_dict(t))

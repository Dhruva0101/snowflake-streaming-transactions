"""Synthetic card-transaction generator.

Usage:
    python generator/transactions.py --count 5          # print JSON lines
    python generator/transactions.py --count 1000 --seed 42 > txns.jsonl

Each transaction looks like a simplified card-network authorization record.
About 1% are flagged as fraud, and fraud skews toward large, foreign, late-night
transactions so there is a real pattern to analyze later.
"""
from __future__ import annotations

import argparse
import json
import random
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone

# (merchant name, merchant category code, typical amount range in USD)
MERCHANTS = [
    ("Fresh Mart Grocery", "5411", (8, 180)),
    ("QuickFuel Gas", "5541", (20, 90)),
    ("Bean There Cafe", "5814", (3, 25)),
    ("Metro Transit", "4111", (2, 15)),
    ("ShopRight Online", "5999", (10, 400)),
    ("Skyline Airlines", "4511", (120, 1500)),
    ("Grand Stay Hotels", "7011", (90, 700)),
    ("TechHub Electronics", "5732", (25, 2500)),
]
COUNTRIES = ["US"] * 18 + ["CA", "GB", "IN", "MX"]  # mostly domestic
CURRENCY = {"US": "USD", "CA": "CAD", "GB": "GBP", "IN": "INR", "MX": "MXN"}
FRAUD_RATE = 0.01


@dataclass
class Transaction:
    txn_id: str
    card_id: str
    merchant: str
    mcc: str
    amount: float
    currency: str
    country: str
    ts: str  # ISO-8601 UTC
    is_fraud: bool


def make_cards(rng: random.Random, n: int = 500) -> list[str]:
    return [f"card_{rng.randrange(10**8):08d}" for _ in range(n)]


def generate(
    count: int,
    seed: int | None = None,
    start: datetime | None = None,
) -> list[Transaction]:
    """Return `count` transactions in timestamp order."""
    rng = random.Random(seed)
    cards = make_cards(rng)
    ts = start or datetime(2026, 1, 1, tzinfo=timezone.utc)
    out: list[Transaction] = []

    for _ in range(count):
        ts += timedelta(seconds=rng.randint(1, 30))
        is_fraud = rng.random() < FRAUD_RATE
        merchant, mcc, (lo, hi) = rng.choice(MERCHANTS)
        amount = rng.uniform(lo, hi)
        country = rng.choice(COUNTRIES)
        when = ts
        if is_fraud:
            # Fraud pattern: bigger amounts, more often abroad, often 1-4am.
            amount *= rng.uniform(2, 5)
            if rng.random() < 0.6:
                country = rng.choice(["GB", "IN", "MX", "CA"])
            if rng.random() < 0.5:
                when = ts.replace(hour=rng.randint(1, 4))
        out.append(
            Transaction(
                txn_id=str(uuid.UUID(int=rng.getrandbits(128))),
                card_id=rng.choice(cards),
                merchant=merchant,
                mcc=mcc,
                amount=round(amount, 2),
                currency=CURRENCY[country],
                country=country,
                ts=when.isoformat(),
                is_fraud=is_fraud,
            )
        )
    return out


def to_dict(txn: Transaction) -> dict:
    return asdict(txn)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    for txn in generate(args.count, seed=args.seed):
        print(json.dumps(to_dict(txn)))


if __name__ == "__main__":
    main()

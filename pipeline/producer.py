"""Publish synthetic transactions to Kafka.

Requires Kafka running locally:  docker compose up -d
Usage:  python pipeline/producer.py --count 1000 --rate 50
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from kafka import KafkaProducer

sys.path.append(str(Path(__file__).resolve().parents[1]))
from generator.transactions import generate, to_dict  # noqa: E402

TOPIC = "card_txns"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--rate", type=float, default=0, help="messages/sec (0 = as fast as possible)")
    parser.add_argument("--bootstrap", default="localhost:9092")
    args = parser.parse_args()

    producer = KafkaProducer(
        bootstrap_servers=args.bootstrap,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8"),
        acks="all",  # wait for the broker to persist each message
    )
    sent = 0
    for txn in generate(args.count):
        # Keying by card_id keeps each card's transactions in order on one partition.
        producer.send(TOPIC, key=txn.card_id, value=to_dict(txn))
        sent += 1
        if args.rate:
            time.sleep(1 / args.rate)
    producer.flush()
    print(f"sent {sent} messages to topic '{TOPIC}'")


if __name__ == "__main__":
    main()

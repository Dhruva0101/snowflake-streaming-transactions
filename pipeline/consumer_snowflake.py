"""Consume transactions from Kafka and load them into Snowflake in micro-batches.

Setup:
  1. Run sql/setup.sql in Snowflake.
  2. cp .env.example .env and fill in your credentials.
  3. python pipeline/consumer_snowflake.py

TODO (Step 1): add a PIPELINE_RUNS audit row per batch (rows, seconds, lag).
"""
from __future__ import annotations

import json
import os
import time

import pandas as pd
import snowflake.connector
from dotenv import load_dotenv
from kafka import KafkaConsumer
from snowflake.connector.pandas_tools import write_pandas

TOPIC = "card_txns"
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "500"))
MAX_WAIT_SECONDS = float(os.getenv("MAX_WAIT_SECONDS", "10"))


def connect():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "XS_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "FIN_DEMO"),
        schema="RAW",
    )


def flush(conn, batch: list[dict]) -> int:
    if not batch:
        return 0
    df = pd.DataFrame(batch)
    df.columns = [c.upper() for c in df.columns]  # Snowflake identifiers are upper-case
    df["TS"] = pd.to_datetime(df["TS"])
    ok, _, nrows, _ = write_pandas(conn, df, "CARD_TXNS", use_logical_type=True)
    if not ok:
        raise RuntimeError("write_pandas failed")
    return nrows


def main() -> None:
    load_dotenv()
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP", "localhost:9092"),
        group_id="snowflake-loader",
        enable_auto_commit=False,  # commit offsets only after Snowflake accepts the batch
        auto_offset_reset="earliest",
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
    )
    conn = connect()
    batch: list[dict] = []
    last_flush = time.monotonic()
    total = 0
    try:
        for msg in consumer:
            batch.append(msg.value)
            if len(batch) >= BATCH_SIZE or time.monotonic() - last_flush > MAX_WAIT_SECONDS:
                total += flush(conn, batch)
                consumer.commit()  # at-least-once: duplicates possible, deduped in dbt
                print(f"loaded {len(batch)} rows (total {total})")
                batch.clear()
                last_flush = time.monotonic()
    finally:
        total += flush(conn, batch)
        conn.close()


if __name__ == "__main__":
    main()

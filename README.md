# Streaming transactions pipeline: Kafka → Snowflake → dbt

[![CI](https://github.com/Dhruva0101/snowflake-streaming-transactions/actions/workflows/ci.yml/badge.svg)](https://github.com/Dhruva0101/snowflake-streaming-transactions/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Tech:** Python · Apache Kafka · Snowflake · dbt · Docker · Jenkins · Kubernetes · pytest

> **Status: in progress.** Step 0 is done: a tested synthetic card-transaction generator, the Snowflake setup script, and the project skeleton (Kafka, consumer, dbt models, Jenkins, Kubernetes). See the roadmap.

A financial-services-style data pipeline: fake card transactions stream through **Kafka**, land in **Snowflake** (streaming and batch paths), and are modeled into a **star schema with dbt**, with data quality tests and lineage. CI/CD runs in **Jenkins**; the consumer is deployed to **Kubernetes**.

## Architecture

```
generator/transactions.py ──▶ Kafka topic "card_txns" ──▶ pipeline/consumer_snowflake.py
        (synthetic data)          (Docker, KRaft)            (micro-batches)
                                                                    │
                                    nightly CSV ── COPY INTO ──▶ Snowflake RAW.CARD_TXNS
                                                                    │
                                                         dbt: stg → fct_transactions,
                                                              dim_card, dim_merchant
                                                         (tests + lineage docs)
```

## Repo layout

| Path | What it is |
|---|---|
| `generator/transactions.py` | Synthetic card transactions (txn_id, card_id, merchant, MCC, amount, currency, timestamp, country, ~1% fraud flag). Works today. |
| `pipeline/producer.py` | Sends generated transactions to Kafka. |
| `pipeline/consumer_snowflake.py` | Reads Kafka in micro-batches and writes to Snowflake. |
| `sql/setup.sql` | Creates the Snowflake database, warehouse, schemas, and raw table. |
| `dbt/` | Staging + mart models and schema tests. |
| `docker-compose.yml` | Local Kafka (KRaft, no ZooKeeper) + Kafka UI. |
| `Jenkinsfile` | CI/CD: lint → tests → dbt build → Docker image. |
| `k8s/` | Kubernetes Deployment for the consumer. |

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. Generator works on its own:
python generator/transactions.py --count 5

# 2. Tests:
pytest -q

# 3. Kafka locally (needs Docker):
docker compose up -d            # Kafka UI at http://localhost:8080
python pipeline/producer.py --count 1000

# 4. Snowflake (free 30-day trial): run sql/setup.sql in a worksheet, then
cp .env.example .env            # fill in your account details
python pipeline/consumer_snowflake.py
```

## Roadmap

- [x] **Step 0:** generator + tests, Snowflake setup SQL, project skeleton, CI
- [ ] **Step 1:** Kafka in Docker; producer → topic; consumer → `RAW.CARD_TXNS`; nightly batch path with `COPY INTO`
- [ ] **Step 2:** dbt on Snowflake: run models, tests (`not_null`, `unique`, `relationships`, `accepted_values`), `dbt docs generate` → screenshot lineage graph here
- [ ] **Step 3:** Jenkins in Docker running the `Jenkinsfile`
- [ ] **Step 4:** consumer on a local Kubernetes cluster (kind or minikube), deployed by Jenkins
- [ ] **Step 5:** observability (`PIPELINE_RUNS` audit table, rows/sec, lag) and a results table here

## Design notes / interview prep

- **Idempotency:** Kafka delivers at least once, so the consumer can see duplicates. The dbt staging model deduplicates on `txn_id`; a production version would `MERGE` on `txn_id`.
- **Micro-batch vs Snowpipe Streaming:** micro-batching with `write_pandas` is simple and cheap on an XS warehouse; Snowpipe Streaming lowers latency. Know the trade-off.
- **Cost control:** XS warehouse with `AUTO_SUSPEND = 60`.

## License

[MIT](LICENSE)

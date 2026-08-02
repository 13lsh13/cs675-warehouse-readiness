# CS-675 Big Data Management Final Project

## Warehouse Inventory and Outbound Order Readiness Analysis System

This project determines whether upcoming outbound warehouse orders can be filled on time, the number of missing pallets, and the earliest expected inventory-availability date.

The repository contains a reproducible synthetic-data generator, a local Apache Spark pipeline, Athena SQL, Docker configuration, Terraform infrastructure, a presentation, and a small demonstration dataset. No company or customer data is used.

## Architecture

`Synthetic CSV -> S3 raw zone -> Spark/EMR Serverless -> Parquet curated zone -> Athena -> dashboard/reporting`

The three source datasets are:

1. `product_reference.csv`: product attributes and storage rules.
2. `shipment_schedule.csv`: planned/actual inbound and outbound shipments.
3. `inventory_transactions.csv`: receipts, shipments, transfers, put-away, and adjustments.

The primary output, `order_readiness.csv`, classifies future outbound orders as:

- **Ready**: enough projected inventory exists, with a safety buffer.
- **At Risk**: the order can be filled, but projected remaining inventory is below the safety-stock threshold.
- **Waiting for Inbound**: inventory is insufficient on the order date, but a later scheduled inbound is expected to cover it.
- **Short**: inventory is insufficient and no known inbound can cover the shortage within the planning horizon.

## Quick start

Generate the included small dataset using only Python's standard library:

```bash
python3 src/generate_synthetic_data.py --output data/sample --transactions 25000 --products 200 --seed 675
```

Run the Spark pipeline with Docker:

```bash
docker compose up --build
```

Or run with a local Spark installation:

```bash
spark-submit src/readiness_pipeline.py \
  --input data/sample \
  --output data/processed \
  --as-of-date 2026-08-01
```

## Big-data scale

The dedicated Spark generator creates the 100-million-record version without collecting rows to one machine:

```bash
spark-submit src/generate_big_data_spark.py \
  --output s3://YOUR-BUCKET/raw \
  --transactions 100000000 \
  --shipments 10000000 \
  --products 10000
```

This generator uses `spark.range`, deterministic expressions, and distributed Parquet writes. Run it on EMR Serverless for the cloud demonstration. The readiness pipeline then repartitions by warehouse and event month and writes Snappy-compressed Parquet.

## Inventory calculation

For each product and warehouse, events are ordered by scheduled date and inbound events are applied before outbound events on the same day:

`projected inventory = current inventory + cumulative inbound - cumulative outbound`

For an outbound order:

`missing pallets = max(planned pallets - available inventory before order, 0)`

## Data-quality controls

The Spark job removes duplicates, rejects missing keys, parses dates, validates enumerated fields, prevents negative planned quantities, quarantines unrealistic quantities, and records rejected rows separately.

## Important limitation

The data and results are a synthetic proof of concept. “Waiting for Inbound” depends on the scheduled inbound arriving as planned. A production system should incorporate reservation priorities, cancellations, lot constraints, and real-time shipment updates.

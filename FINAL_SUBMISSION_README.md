# CS-675 Final Project Submission

**Student:** Shuhao Lin  
**Course:** CS-675 Big Data Management  
**Project:** Warehouse Inventory and Outbound Order Readiness Analysis System

## Submission summary

This submission contains the presentation, source code, infrastructure-as-code, synthetic input data, processed outputs, SQL analysis, charts, speaker script, and reproducibility instructions for the final project.

The system answers the main business question:

> Will the warehouse have enough inventory to complete each upcoming outbound order, and if not, how many pallets will be missing and when is inventory expected to become available?

No confidential company data is included. All data is synthetic and reproducible.

## Instructor-requirement checklist

| Requirement | Included artifact |
|---|---|
| Presentation slides | `artifacts/CS675_Warehouse_Inventory_Order_Readiness_Shuhao_Lin.pptx` |
| Important aspects covered | This file and the project-requirements section below |
| All application source code | `src/` and `build_cs675_presentation.py` |
| Infrastructure source code | `terraform/`, `Dockerfile`, and `docker-compose.yml` |
| Guidelines and run instructions | `README.md` and this file |
| Input data | `data/sample/product_reference.csv`, `shipment_schedule.csv`, and `inventory_transactions.csv` |
| Output files | `data/sample/order_readiness_expected.csv` and `data/processed/` |
| SQL queries | `sql/athena_analysis.sql` |
| Self-contained execution | Docker configuration, pinned Python requirements, generators, processing code, and sample data are included |
| Extra artifacts | Charts and two presentation scripts under `artifacts/` |

## Important project requirements covered

1. **Big-data problem:** Event-level warehouse inventory and shipment readiness across products, warehouses, and dates.
2. **Three related datasets:** Product reference, shipment schedule, and inventory transactions.
3. **Data integration:** Joins use product ID, warehouse ID, shipment ID, and date.
4. **Data quality:** Spark validates required keys, dates, quantities, enumerated fields, duplicates, and unrealistic values. Invalid rows go to quarantine outputs.
5. **Distributed processing:** PySpark performs joins, aggregations, chronological window calculations, and readiness classification.
6. **Business calculation:** Projected inventory equals current inventory plus cumulative inbound minus cumulative outbound.
7. **Business output:** Orders are classified as Ready, At Risk, Waiting for Inbound, or Short, with missing pallets and earliest expected availability.
8. **Efficient storage:** Processed output uses Snappy-compressed, partitioned Parquet.
9. **Cloud architecture:** S3 stores raw and curated data, EMR Serverless runs Spark, Glue provides catalog metadata, and Athena queries results.
10. **Infrastructure as code:** Terraform defines the S3, Glue, Athena, IAM, and EMR Serverless resources.
11. **Scale design:** A separate distributed generator uses `spark.range()` for a planned 100-million-transaction cloud test.
12. **Privacy:** Every included record is synthetic; no customer, employee, product, or shipment record comes from a real company system.

## Included data and results

### Input data

| Dataset | Records | Purpose |
|---|---:|---|
| Product reference | 200 | Product category, packaging, storage area, and safety stock |
| Shipment schedule | 3,125 | Inbound/outbound plans, actual quantity, status, and date |
| Inventory transactions | 25,000 | Receipts, shipments, transfers, put-away, and adjustments |

### Spark test output

The validated local Spark execution evaluated 684 upcoming outbound orders:

| Status | Orders | Missing pallets |
|---|---:|---:|
| Ready | 509 | 0 |
| At Risk | 51 | 0 |
| Waiting for Inbound | 31 | 603 |
| Short | 93 | 1,921 |
| **Total** | **684** | **2,524** |

Processed output is under `data/processed/`, partitioned by warehouse and event month.

## Reproduce the project

### Recommended: Docker

Requirements: Docker Desktop with Docker Compose.

```bash
docker compose up --build
```

This runs `src/readiness_pipeline.py` against the included sample and writes processed output under `data/processed/`.

### Standard Python and Spark installation

Requirements: Python 3.9+, Java 17 or 21, and Apache Spark 3.5.1.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 src/generate_synthetic_data.py --output data/sample --transactions 25000 --products 200 --seed 675
spark-submit src/readiness_pipeline.py --input data/sample --output data/processed --as-of-date 2026-08-01
```

Rebuild the presentation:

```bash
MPLBACKEND=Agg python3 build_cs675_presentation.py
```

## Main source files

- `src/generate_synthetic_data.py`: reproducible local CSV generator.
- `src/generate_big_data_spark.py`: distributed Parquet generator for the large-scale test.
- `src/readiness_pipeline.py`: validation, joins, projected-inventory calculation, classification, and output.
- `sql/athena_analysis.sql`: operational SQL queries for the curated data.
- `terraform/main.tf`: reproducible AWS architecture.
- `build_cs675_presentation.py`: presentation and chart generator.

## Repository submission

The folder is ready to upload to a GitHub repository. Exclude `.deps/`, `.venv/`, caches, and operating-system metadata. Submit the repository URL together with the packaged ZIP file if the assignment portal allows both.

## Limitations

- Results are a proof of concept based on synthetic data.
- Scheduled inbound availability assumes shipments arrive as planned.
- A production system would also incorporate reservations, order priority, lot constraints, cancellations, and live warehouse-management-system updates.
- The 100-million-record generator is included, but the full cloud-scale run requires an AWS account and incurs AWS charges.

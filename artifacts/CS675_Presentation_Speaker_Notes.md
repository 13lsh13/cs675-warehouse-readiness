# CS-675 Presentation Speaker Notes

## Slide 1: WAREHOUSE INVENTORY &OUTBOUND ORDER READINESS

Good afternoon. My final project is a Warehouse Inventory and Outbound Order Readiness Analysis System. It combines warehouse operations knowledge with Spark, SQL, AWS, and reproducible infrastructure.

## Slide 2: BUSINESS PROBLEM

Warehouses must consider timing, not only the current balance. An order can look short today but become ready after an inbound receipt—or look ready until an earlier outbound consumes the stock.

## Slide 3: DATA MODEL

The design separates product master data, shipment plans, and executed inventory events. Product ID and warehouse ID connect the tables; shipment ID links scheduled shipments to completed movements.

## Slide 4: CORE CALCULATION

For each product and warehouse, I calculate current inventory from completed transactions, then apply future inbound and outbound events by date. Inbound is processed before outbound on the same date.

## Slide 5: DECISION LOGIC

The status is designed for supervisors and planners. Ready and At Risk distinguish healthy orders from orders that leave little safety stock. Waiting for Inbound separates timing issues from unresolved shortages.

## Slide 6: PROCESSING PIPELINE

The Spark job reads explicit schemas, applies data-quality rules, calculates current inventory, orders future events with window functions, assigns readiness status, and writes partitioned Parquet.

## Slide 7: PLATFORM ARCHITECTURE

I first test the logic locally with Docker and a smaller dataset. The cloud version stores raw and curated zones in S3, runs Spark on EMR Serverless, and exposes results through Athena.

## Slide 8: SYNTHETIC DATA

The included sample uses a fixed random seed and an as-of date of August 1, 2026. It represents three warehouses and realistic inbound, outbound, transfer, put-away, adjustment, and delay patterns.

## Slide 9: DEMONSTRATION RESULTS

Of 684 upcoming outbound orders, 511 are ready. The remaining 173 are at risk, waiting for inbound, or short. Total modeled shortage exposure is 2,288 pallets.

## Slide 10: ANALYTICS

The curated tables support daily exception reporting and broader product analysis. These example results are produced from the same synthetic schedule included with the project.

## Slide 11: BIG-DATA STRATEGY

The large test uses the same schemas and logic, but generates partitioned files and distributes processing across Spark executors. The goal is to demonstrate volume, distributed computation, and efficient query storage—not merely create one oversized CSV.

## Slide 12: CONCLUSION

The expected result is a practical analytics system that finds inventory constraints before orders are loaded. It demonstrates data modeling, quality controls, distributed processing, cloud design, SQL analytics, and business interpretation.


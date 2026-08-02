# CS-675 Direct Presentation Script

## Slide 1 — Introduction

Good afternoon, everyone.

For my final project, I plan to build a **Warehouse Inventory and Outbound Order Readiness Analysis System**.

I selected this topic because it connects directly to my warehouse operations experience. In a warehouse, one common challenge is determining whether there is enough inventory available to complete upcoming outbound orders.

## Slide 2 — Business Problem

It is not always enough to look at the current inventory. We also need to consider future inbound shipments, scheduled outbound orders, inventory transfers, and the timing of each transaction.

The main question for my project is:

**Will the warehouse have enough inventory to complete each upcoming outbound order, and if not, how many pallets will be missing?**

The system will also determine when enough inventory is expected to become available.

## Slide 3 — Synthetic Data and Privacy

To protect company information, I will not use actual customer names, employee information, product numbers, or shipment records. Instead, I plan to create synthetic data that follows realistic warehouse operating patterns.

My project will use three related datasets.

The first dataset will contain inventory transactions. These records will include product ID, warehouse location, transaction date, transaction type, and pallet quantity. Transaction types may include inbound receipts, outbound shipments, inventory transfers, put-away activities, and inventory adjustments.

The second dataset will contain the inbound and outbound shipment schedule. It will include the shipment ID, product ID, scheduled date, planned pallet quantity, actual quantity, shipment type, and shipment status.

The third dataset will be a product reference table. It will contain fields such as product category, packaging type, standard pallet quantity, and storage area.

These datasets will be joined mainly by product ID, warehouse ID, shipment ID, and date.

## Slide 4 — Inventory Calculation

The main calculation in the project will be:

**Projected inventory equals current inventory, plus cumulative inbound shipments, minus cumulative outbound shipments.**

For example, imagine a product currently has 20 pallets available. There is an outbound order for 15 pallets tomorrow, an inbound shipment of 10 pallets the following day, and another outbound order for 18 pallets after that.

After the first order, five pallets will remain. After receiving the inbound shipment, the warehouse will have 15 pallets. Because the next order requires 18 pallets, the system will identify a shortage of three pallets.

## Slide 5 — Readiness Status

The order will then be classified into one of four statuses:

**Ready, At Risk, Short, or Waiting for Inbound.**

## Slide 6 — Operational Questions

I also plan to answer several operational questions.

First, which upcoming outbound orders do not have enough inventory?

Second, how many pallets are missing for each order?

Third, what is the earliest date when enough inventory will become available?

Fourth, which products have the highest inbound and outbound volume?

Finally, which products experience the most inventory adjustments, shortages, or shipment delays?

## Slide 7 — Spark Data Processing

For data preprocessing, I will use Apache Spark to handle missing values, duplicate records, invalid quantities, incorrect dates, and unrealistic transaction values.

I will first develop and test the project locally using Docker and a smaller Spark dataset. After the calculations and joins work correctly, I will deploy the full version on AWS.

## Slide 8 — AWS Architecture

Amazon S3 will store the raw and processed data. Spark or EMR Serverless will process the large dataset, and Amazon Athena will be used to query the final results.

The processed data will be stored in Parquet format because it is more efficient for Spark and Athena than CSV.

The full cloud version will contain at least 100 million records to meet the big-data requirement. Terraform will also be used to create the AWS resources in a reproducible way.

## Slide 9 — Optional Dashboard

As an optional feature, I plan to create a simple dashboard. It may show current inventory, inbound and outbound volume, orders at risk, missing pallet quantities, and inventory trends over time.

## Slide 10 — Current Progress

So far, I have selected the topic, defined the datasets, identified the join keys, developed the inventory calculation, and planned the main analytical questions.

## Slide 11 — Next Steps

My next steps are to confirm the synthetic-data approach, create the dataset schemas, generate a small sample, build the Spark preprocessing pipeline, and test the inventory forecast calculation.

## Slide 12 — Expected Result and Conclusion

The expected result is a practical warehouse analytics system that can identify inventory shortages before outbound orders are scheduled or loaded.

This project combines my warehouse experience with Spark, SQL, cloud computing, data engineering, and business intelligence. It will also give me a project that I can discuss in future interviews for data analyst, business intelligence, and operations analytics roles.

Thank you.

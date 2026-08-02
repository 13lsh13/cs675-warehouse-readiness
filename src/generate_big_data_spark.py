#!/usr/bin/env python3
"""Distributed synthetic generator for the CS-675 100M-record scale test."""

import argparse
from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--transactions", type=int, default=100_000_000)
    parser.add_argument("--shipments", type=int, default=10_000_000)
    parser.add_argument("--products", type=int, default=10_000)
    parser.add_argument("--partitions", type=int, default=400)
    return parser.parse_args()


def main():
    args = arguments()
    spark = (SparkSession.builder.appName("CS675-Distributed-Synthetic-Generator")
             .config("spark.sql.adaptive.enabled", "true").getOrCreate())
    warehouses = F.array(F.lit("WH-EAST"), F.lit("WH-CENTRAL"), F.lit("WH-WEST"))
    categories = F.array(F.lit("Beverage"), F.lit("Food"), F.lit("Household"), F.lit("Paper"), F.lit("Personal Care"))
    types = F.array(F.lit("RECEIPT"), F.lit("SHIPMENT"), F.lit("TRANSFER_IN"), F.lit("TRANSFER_OUT"), F.lit("PUTAWAY"), F.lit("ADJUSTMENT"))

    products = (spark.range(args.products, numPartitions=max(8, args.partitions // 20))
        .select(
            F.format_string("PRD-%05d", F.col("id") + 1).alias("product_id"),
            F.element_at(categories, (F.col("id") % 5 + 1).cast("int")).alias("product_category"),
            F.when(F.col("id") % 4 == 0, "Cases").when(F.col("id") % 4 == 1, "Drums").when(F.col("id") % 4 == 2, "Bags").otherwise("Cartons").alias("packaging_type"),
            (F.lit(36) + (F.col("id") % 5) * 12).cast("int").alias("standard_units_per_pallet"),
            F.concat(F.lit("AREA-"), (F.col("id") % 12 + 1).cast("string")).alias("storage_area"),
            (F.col("id") % 28 + 8).cast("int").alias("safety_stock_pallets")))

    shipments = (spark.range(args.shipments, numPartitions=args.partitions)
        .select(
            F.format_string("SHP-%010d", F.col("id") + 1).alias("shipment_id"),
            F.format_string("PRD-%05d", F.col("id") % args.products + 1).alias("product_id"),
            F.element_at(warehouses, (F.col("id") % 3 + 1).cast("int")).alias("warehouse_id"),
            F.date_add(F.lit("2026-04-01").cast("date"), (F.col("id") % 211).cast("int")).alias("scheduled_date"),
            (F.col("id") % 52 + 4).cast("int").alias("planned_pallet_quantity"),
            F.when(F.col("id") % 211 <= 122, (F.col("id") % 52 + 4).cast("int")).cast("int").alias("actual_pallet_quantity"),
            F.when(F.col("id") % 100 < 47, "INBOUND").otherwise("OUTBOUND").alias("shipment_type"),
            F.when(F.col("id") % 97 == 0, "CANCELLED").when(F.col("id") % 31 == 0, "DELAYED")
             .when(F.col("id") % 211 <= 122, "COMPLETED").otherwise("SCHEDULED").alias("shipment_status")))

    transactions = (spark.range(args.transactions, numPartitions=args.partitions)
        .select(
            F.format_string("TX-%012d", F.col("id") + 1).alias("transaction_id"),
            F.when(F.col("id") % 4 < 2, F.format_string("SHP-%010d", F.col("id") % args.shipments + 1)).otherwise(F.lit(None)).alias("shipment_id"),
            F.format_string("PRD-%05d", F.col("id") % args.products + 1).alias("product_id"),
            F.element_at(warehouses, (F.col("id") % 3 + 1).cast("int")).alias("warehouse_id"),
            F.date_add(F.lit("2026-04-01").cast("date"), (F.col("id") % 123).cast("int")).alias("transaction_date"),
            F.element_at(types, (F.col("id") % 6 + 1).cast("int")).alias("transaction_type"),
            F.when(F.col("id") % 6 == 1, -(F.col("id") % 48 + 1))
             .when(F.col("id") % 6 == 3, -(F.col("id") % 18 + 1))
             .when(F.col("id") % 6 == 4, F.lit(0))
             .when(F.col("id") % 6 == 5, F.when(F.col("id") % 2 == 0, 1).otherwise(-1) * (F.col("id") % 8 + 1))
             .otherwise(F.col("id") % 55 + 1).cast("int").alias("pallet_quantity"),
            F.concat(F.lit("LOC-"), (F.col("id") % 40 + 1).cast("string")).alias("source_location"),
            F.concat(F.lit("LOC-"), (F.col("id") % 40 + 2).cast("string")).alias("destination_location")))

    products.write.mode("overwrite").parquet(f"{args.output}/product_reference")
    (shipments.withColumn("event_month", F.date_format("scheduled_date", "yyyy-MM"))
     .write.mode("overwrite").partitionBy("warehouse_id", "event_month").parquet(f"{args.output}/shipment_schedule"))
    (transactions.withColumn("event_month", F.date_format("transaction_date", "yyyy-MM"))
     .write.mode("overwrite").partitionBy("warehouse_id", "event_month").parquet(f"{args.output}/inventory_transactions"))
    spark.stop()


if __name__ == "__main__":
    main()

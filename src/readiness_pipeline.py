#!/usr/bin/env python3
"""PySpark pipeline for warehouse outbound-order readiness."""

import argparse
from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DateType, IntegerType, StringType, StructField, StructType,
)

AS_OF_DEFAULT = "2026-08-01"

product_schema = StructType([
    StructField("product_id", StringType()), StructField("product_category", StringType()),
    StructField("packaging_type", StringType()), StructField("standard_units_per_pallet", IntegerType()),
    StructField("storage_area", StringType()), StructField("safety_stock_pallets", IntegerType()),
])
shipment_schema = StructType([
    StructField("shipment_id", StringType()), StructField("product_id", StringType()),
    StructField("warehouse_id", StringType()), StructField("scheduled_date", DateType()),
    StructField("planned_pallet_quantity", IntegerType()), StructField("actual_pallet_quantity", IntegerType()),
    StructField("shipment_type", StringType()), StructField("shipment_status", StringType()),
])
transaction_schema = StructType([
    StructField("transaction_id", StringType()), StructField("shipment_id", StringType()),
    StructField("product_id", StringType()), StructField("warehouse_id", StringType()),
    StructField("transaction_date", DateType()), StructField("transaction_type", StringType()),
    StructField("pallet_quantity", IntegerType()), StructField("source_location", StringType()),
    StructField("destination_location", StringType()),
])


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/sample")
    parser.add_argument("--output", default="data/processed")
    parser.add_argument("--as-of-date", default=AS_OF_DEFAULT)
    return parser.parse_args()


def valid_and_rejected(df, predicate):
    return df.filter(predicate), df.filter(~predicate | predicate.isNull())


def main():
    args = parse_args()
    spark = (SparkSession.builder.appName("CS675-Warehouse-Readiness")
             .config("spark.sql.adaptive.enabled", "true")
             .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
             .getOrCreate())
    as_of = F.to_date(F.lit(args.as_of_date))

    products_raw = spark.read.option("header", True).schema(product_schema).csv(f"{args.input}/product_reference.csv")
    shipments_raw = spark.read.option("header", True).schema(shipment_schema).csv(f"{args.input}/shipment_schedule.csv")
    tx_raw = spark.read.option("header", True).schema(transaction_schema).csv(f"{args.input}/inventory_transactions.csv")

    products = products_raw.dropDuplicates(["product_id"])
    shipments_base = shipments_raw.dropDuplicates(["shipment_id"])
    tx_base = tx_raw.dropDuplicates(["transaction_id"])

    shipment_ok = (
        F.col("shipment_id").isNotNull() & F.col("product_id").isNotNull() &
        F.col("warehouse_id").isNotNull() & F.col("scheduled_date").isNotNull() &
        F.col("planned_pallet_quantity").between(1, 500) &
        F.col("shipment_type").isin("INBOUND", "OUTBOUND") &
        F.col("shipment_status").isin("SCHEDULED", "COMPLETED", "DELAYED", "CANCELLED")
    )
    tx_ok = (
        F.col("transaction_id").isNotNull() & F.col("product_id").isNotNull() &
        F.col("warehouse_id").isNotNull() & F.col("transaction_date").isNotNull() &
        (F.abs(F.col("pallet_quantity")) <= 500) &
        F.col("transaction_type").isin("RECEIPT", "SHIPMENT", "TRANSFER_IN", "TRANSFER_OUT", "PUTAWAY", "ADJUSTMENT")
    )
    shipments, rejected_shipments = valid_and_rejected(shipments_base, shipment_ok)
    transactions, rejected_transactions = valid_and_rejected(tx_base, tx_ok)

    current = (transactions.filter(F.col("transaction_date") <= as_of)
               .groupBy("product_id", "warehouse_id")
               .agg(F.sum("pallet_quantity").alias("current_inventory"))
               .withColumn("current_inventory", F.greatest(F.col("current_inventory"), F.lit(0))))

    future = (shipments
              .filter((F.col("scheduled_date") > as_of) & (F.col("shipment_status") != "CANCELLED"))
              .join(products.select("product_id", "safety_stock_pallets"), "product_id", "left")
              .join(current, ["product_id", "warehouse_id"], "left")
              .fillna({"current_inventory": 0, "safety_stock_pallets": 0})
              .withColumn("event_priority", F.when(F.col("shipment_type") == "INBOUND", 0).otherwise(1))
              .withColumn("signed_quantity", F.when(F.col("shipment_type") == "INBOUND", F.col("planned_pallet_quantity"))
                          .otherwise(-F.col("planned_pallet_quantity"))))

    event_window = (Window.partitionBy("product_id", "warehouse_id")
                    .orderBy("scheduled_date", "event_priority", "shipment_id")
                    .rowsBetween(Window.unboundedPreceding, -1))
    scored = (future
              .withColumn("prior_net_events", F.coalesce(F.sum("signed_quantity").over(event_window), F.lit(0)))
              .withColumn("available_before_order", F.greatest(F.col("current_inventory") + F.col("prior_net_events"), F.lit(0)))
              .withColumn("missing_pallets", F.when(F.col("shipment_type") == "OUTBOUND",
                          F.greatest(F.col("planned_pallet_quantity") - F.col("available_before_order"), F.lit(0))).otherwise(0))
              .withColumn("projected_inventory_after_order", F.greatest(F.col("available_before_order") + F.col("signed_quantity"), F.lit(0))))

    outbound = scored.filter(F.col("shipment_type") == "OUTBOUND").alias("o")
    later_inbound = scored.filter(F.col("shipment_type") == "INBOUND").alias("i")
    availability = (outbound.filter(F.col("o.missing_pallets") > 0)
                    .join(later_inbound,
                          (F.col("o.product_id") == F.col("i.product_id")) &
                          (F.col("o.warehouse_id") == F.col("i.warehouse_id")) &
                          (F.col("i.scheduled_date") > F.col("o.scheduled_date")) &
                          (F.col("i.projected_inventory_after_order") >= F.col("o.planned_pallet_quantity")), "left")
                    .groupBy(F.col("o.shipment_id").alias("shipment_id"))
                    .agg(F.min("i.scheduled_date").alias("earliest_inbound_date")))

    readiness = (outbound.join(availability, "shipment_id", "left")
                 .withColumn("readiness_status",
                    F.when(F.col("missing_pallets") == 0,
                        F.when(F.col("projected_inventory_after_order") < F.col("safety_stock_pallets"), "AT_RISK").otherwise("READY"))
                     .when(F.col("earliest_inbound_date").isNotNull(), "WAITING_FOR_INBOUND")
                     .otherwise("SHORT"))
                 .withColumn("earliest_available_date",
                    F.when(F.col("missing_pallets") == 0, F.col("scheduled_date")).otherwise(F.col("earliest_inbound_date")))
                 .withColumn("as_of_date", as_of)
                 .select("shipment_id", "product_id", "warehouse_id", "scheduled_date",
                         "planned_pallet_quantity", "available_before_order", "projected_inventory_after_order",
                         "missing_pallets", "readiness_status", "earliest_available_date", "as_of_date"))

    (readiness.withColumn("event_month", F.date_format("scheduled_date", "yyyy-MM"))
     .repartition("warehouse_id", "event_month")
     .write.mode("overwrite").partitionBy("warehouse_id", "event_month")
     .option("compression", "snappy").parquet(f"{args.output}/order_readiness"))
    current.write.mode("overwrite").parquet(f"{args.output}/current_inventory")
    rejected_shipments.write.mode("overwrite").json(f"{args.output}/quarantine/shipments")
    rejected_transactions.write.mode("overwrite").json(f"{args.output}/quarantine/transactions")

    readiness.groupBy("readiness_status").agg(F.count("*").alias("orders"), F.sum("missing_pallets").alias("missing_pallets")).show()
    spark.stop()


if __name__ == "__main__":
    main()

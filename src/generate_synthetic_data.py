#!/usr/bin/env python3
"""Generate privacy-safe warehouse data with deterministic operational patterns."""

from __future__ import annotations

import argparse
import csv
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

AS_OF = date(2026, 8, 1)
WAREHOUSES = ["WH-EAST", "WH-CENTRAL", "WH-WEST"]
CATEGORIES = ["Beverage", "Food", "Household", "Paper", "Personal Care"]
PACKAGING = ["Cases", "Drums", "Bags", "Cartons"]
AREAS = ["Ambient-A", "Ambient-B", "Secure", "High-Bay", "Temperature-Controlled"]


def write_rows(path: Path, fields: list[str], rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def generate_products(rng: random.Random, count: int) -> list[dict]:
    rows = []
    for i in range(1, count + 1):
        category = rng.choice(CATEGORIES)
        rows.append({
            "product_id": f"PRD-{i:05d}",
            "product_category": category,
            "packaging_type": rng.choice(PACKAGING),
            "standard_units_per_pallet": rng.choice([36, 48, 60, 72, 96]),
            "storage_area": "Temperature-Controlled" if category == "Food" and rng.random() < .28 else rng.choice(AREAS[:-1]),
            "safety_stock_pallets": rng.randint(8, 35),
        })
    return rows


def generate_shipments(rng: random.Random, products: list[dict], transactions_target: int):
    start = AS_OF - timedelta(days=120)
    end = AS_OF + timedelta(days=90)
    day_count = (end - start).days + 1
    shipment_count = max(1600, transactions_target // 8)
    shipments, transactions = [], []
    inventory = defaultdict(int)
    tx_number = 1

    # Establish realistic opening inventory for every product/warehouse pair.
    for product in products:
        for warehouse in WAREHOUSES:
            qty = rng.randint(35, 180)
            inventory[(product["product_id"], warehouse)] += qty
            transactions.append({
                "transaction_id": f"TX-{tx_number:09d}", "shipment_id": "",
                "product_id": product["product_id"], "warehouse_id": warehouse,
                "transaction_date": start.isoformat(), "transaction_type": "ADJUSTMENT",
                "pallet_quantity": qty, "source_location": "OPENING", "destination_location": product["storage_area"],
            })
            tx_number += 1

    for i in range(1, shipment_count + 1):
        product = rng.choice(products)
        warehouse = rng.choice(WAREHOUSES)
        scheduled = start + timedelta(days=rng.randrange(day_count))
        shipment_type = "INBOUND" if rng.random() < .47 else "OUTBOUND"
        planned = rng.randint(4, 55) if shipment_type == "INBOUND" else rng.randint(3, 48)
        historical = scheduled <= AS_OF
        delayed = rng.random() < .09
        cancelled = rng.random() < .025
        if cancelled:
            status = "CANCELLED"
        elif historical:
            status = "DELAYED" if delayed and scheduled > AS_OF - timedelta(days=4) else "COMPLETED"
        else:
            status = "DELAYED" if delayed else "SCHEDULED"
        actual = ""
        shipment_id = f"SHP-{i:08d}"
        if status == "COMPLETED":
            actual_qty = max(0, planned + rng.choice([-3, -2, -1, 0, 0, 0, 1, 2]))
            actual = actual_qty
            signed = actual_qty if shipment_type == "INBOUND" else -actual_qty
            transaction_date = scheduled + timedelta(days=rng.choice([0, 0, 0, 1]))
            if transaction_date <= AS_OF:
                inventory[(product["product_id"], warehouse)] += signed
            transactions.append({
                "transaction_id": f"TX-{tx_number:09d}", "shipment_id": shipment_id,
                "product_id": product["product_id"], "warehouse_id": warehouse,
                "transaction_date": transaction_date.isoformat(),
                "transaction_type": "RECEIPT" if shipment_type == "INBOUND" else "SHIPMENT",
                "pallet_quantity": signed, "source_location": "DOCK" if shipment_type == "INBOUND" else product["storage_area"],
                "destination_location": product["storage_area"] if shipment_type == "INBOUND" else "CUSTOMER",
            })
            tx_number += 1
        shipments.append({
            "shipment_id": shipment_id, "product_id": product["product_id"], "warehouse_id": warehouse,
            "scheduled_date": scheduled.isoformat(), "planned_pallet_quantity": planned,
            "actual_pallet_quantity": actual, "shipment_type": shipment_type, "shipment_status": status,
        })

    # Add operational events until the requested transaction count is reached.
    while len(transactions) < transactions_target:
        product = rng.choice(products)
        warehouse = rng.choice(WAREHOUSES)
        event_date = start + timedelta(days=rng.randrange((AS_OF - start).days + 1))
        event_type = rng.choices(["PUTAWAY", "TRANSFER_IN", "TRANSFER_OUT", "ADJUSTMENT"], [45, 18, 18, 19])[0]
        qty = rng.randint(1, 18)
        if event_type in {"TRANSFER_OUT"}:
            qty = -qty
        elif event_type == "ADJUSTMENT":
            qty = rng.choice([-1, 1]) * rng.randint(1, 8)
        # Put-away changes location but not total warehouse inventory; zero is intentional.
        inventory_qty = 0 if event_type == "PUTAWAY" else qty
        inventory[(product["product_id"], warehouse)] += inventory_qty
        transactions.append({
            "transaction_id": f"TX-{tx_number:09d}", "shipment_id": "",
            "product_id": product["product_id"], "warehouse_id": warehouse,
            "transaction_date": event_date.isoformat(), "transaction_type": event_type,
            "pallet_quantity": inventory_qty, "source_location": "STAGING",
            "destination_location": product["storage_area"],
        })
        tx_number += 1
    return shipments, transactions, inventory


def readiness_rows(shipments: list[dict], inventory: dict, products: list[dict]) -> list[dict]:
    safety = {p["product_id"]: p["safety_stock_pallets"] for p in products}
    future = [s for s in shipments if s["scheduled_date"] > AS_OF.isoformat() and s["shipment_status"] != "CANCELLED"]
    grouped = defaultdict(list)
    for shipment in future:
        grouped[(shipment["product_id"], shipment["warehouse_id"])].append(shipment)
    output = []
    for key, events in grouped.items():
        events.sort(key=lambda x: (x["scheduled_date"], 0 if x["shipment_type"] == "INBOUND" else 1, x["shipment_id"]))
        balance = max(0, inventory[key])
        for index, event in enumerate(events):
            qty = int(event["planned_pallet_quantity"])
            before = balance
            if event["shipment_type"] == "INBOUND":
                balance += qty
                continue
            missing = max(qty - before, 0)
            remaining = max(before - qty, 0)
            earliest = event["scheduled_date"] if missing == 0 else ""
            if missing == 0:
                status = "AT_RISK" if remaining < safety[key[0]] else "READY"
            else:
                lookahead = before
                for later in events[index + 1:]:
                    later_qty = int(later["planned_pallet_quantity"])
                    lookahead += later_qty if later["shipment_type"] == "INBOUND" else -later_qty
                    if lookahead >= qty:
                        earliest = later["scheduled_date"]
                        break
                status = "WAITING_FOR_INBOUND" if earliest else "SHORT"
            output.append({
                "shipment_id": event["shipment_id"], "product_id": key[0], "warehouse_id": key[1],
                "scheduled_date": event["scheduled_date"], "planned_pallet_quantity": qty,
                "available_before_order": before, "projected_inventory_after_order": remaining,
                "missing_pallets": missing, "readiness_status": status,
                "earliest_available_date": earliest, "as_of_date": AS_OF.isoformat(),
            })
            balance = remaining
    return sorted(output, key=lambda x: (x["scheduled_date"], x["warehouse_id"], x["shipment_id"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/sample"))
    parser.add_argument("--transactions", type=int, default=25000)
    parser.add_argument("--products", type=int, default=200)
    parser.add_argument("--parts", type=int, default=1, help="Reserved for large partitioned generation")
    parser.add_argument("--seed", type=int, default=675)
    args = parser.parse_args()
    if args.transactions < args.products * len(WAREHOUSES):
        parser.error("transactions must cover at least one opening record per product and warehouse")
    rng = random.Random(args.seed)
    products = generate_products(rng, args.products)
    shipments, transactions, inventory = generate_shipments(rng, products, args.transactions)
    readiness = readiness_rows(shipments, inventory, products)
    write_rows(args.output / "product_reference.csv", list(products[0]), products)
    write_rows(args.output / "shipment_schedule.csv", list(shipments[0]), shipments)
    write_rows(args.output / "inventory_transactions.csv", list(transactions[0]), transactions)
    write_rows(args.output / "order_readiness_expected.csv", list(readiness[0]), readiness)
    print(f"Generated {len(products):,} products, {len(shipments):,} shipments, {len(transactions):,} transactions, and {len(readiness):,} readiness rows in {args.output}")


if __name__ == "__main__":
    main()

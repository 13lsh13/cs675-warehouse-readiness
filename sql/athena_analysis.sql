-- Replace cs675_curated with the Glue/Athena database created by Terraform.

-- 1. Upcoming outbound orders that need attention
SELECT shipment_id, product_id, warehouse_id, scheduled_date,
       planned_pallet_quantity, missing_pallets, readiness_status,
       earliest_available_date
FROM cs675_curated.order_readiness
WHERE readiness_status IN ('AT_RISK', 'SHORT', 'WAITING_FOR_INBOUND')
ORDER BY scheduled_date, missing_pallets DESC;

-- 2. Shortage exposure by warehouse
SELECT warehouse_id,
       COUNT_IF(readiness_status IN ('SHORT', 'WAITING_FOR_INBOUND')) AS constrained_orders,
       SUM(missing_pallets) AS missing_pallets
FROM cs675_curated.order_readiness
GROUP BY warehouse_id
ORDER BY missing_pallets DESC;

-- 3. Highest planned product volume
SELECT product_id,
       SUM(CASE WHEN shipment_type = 'INBOUND' THEN planned_pallet_quantity ELSE 0 END) AS inbound_pallets,
       SUM(CASE WHEN shipment_type = 'OUTBOUND' THEN planned_pallet_quantity ELSE 0 END) AS outbound_pallets
FROM cs675_curated.shipment_schedule
WHERE shipment_status <> 'CANCELLED'
GROUP BY product_id
ORDER BY inbound_pallets + outbound_pallets DESC
LIMIT 20;

-- 4. Products with the most adjustments
SELECT product_id, COUNT(*) AS adjustment_events,
       SUM(ABS(pallet_quantity)) AS adjusted_pallets
FROM cs675_curated.inventory_transactions
WHERE transaction_type = 'ADJUSTMENT'
GROUP BY product_id
ORDER BY adjusted_pallets DESC
LIMIT 20;

-- 5. Shipment-delay rate
SELECT warehouse_id, shipment_type,
       COUNT_IF(shipment_status = 'DELAYED') AS delayed_shipments,
       COUNT(*) AS total_shipments,
       ROUND(100.0 * COUNT_IF(shipment_status = 'DELAYED') / COUNT(*), 2) AS delay_rate_pct
FROM cs675_curated.shipment_schedule
GROUP BY warehouse_id, shipment_type;

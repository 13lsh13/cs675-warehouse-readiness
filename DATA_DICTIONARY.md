# Data Dictionary

## `product_reference.csv`

| Field | Type | Description |
|---|---|---|
| `product_id` | string | Synthetic product identifier; primary key |
| `product_category` | string | General product family |
| `packaging_type` | string | Cases, drums, bags, or cartons |
| `standard_units_per_pallet` | integer | Standard units stored on one pallet |
| `storage_area` | string | Warehouse storage-zone requirement |
| `safety_stock_pallets` | integer | Minimum desired remaining inventory |

## `shipment_schedule.csv`

| Field | Type | Description |
|---|---|---|
| `shipment_id` | string | Synthetic shipment identifier; primary key |
| `product_id` | string | Product reference key |
| `warehouse_id` | string | Warehouse receiving or shipping the pallets |
| `scheduled_date` | date | Planned shipment date in ISO format |
| `planned_pallet_quantity` | integer | Scheduled number of pallets |
| `actual_pallet_quantity` | integer/null | Completed number of pallets when available |
| `shipment_type` | string | `INBOUND` or `OUTBOUND` |
| `shipment_status` | string | `SCHEDULED`, `COMPLETED`, `DELAYED`, or `CANCELLED` |

## `inventory_transactions.csv`

| Field | Type | Description |
|---|---|---|
| `transaction_id` | string | Synthetic transaction identifier; primary key |
| `shipment_id` | string/null | Related shipment when applicable |
| `product_id` | string | Product reference key |
| `warehouse_id` | string | Warehouse where the event occurred |
| `transaction_date` | date | Effective transaction date |
| `transaction_type` | string | Receipt, shipment, transfer, put-away, or adjustment |
| `pallet_quantity` | integer | Signed inventory change; inbound is positive and outbound is negative |
| `source_location` | string | Starting warehouse location or external source |
| `destination_location` | string | Ending warehouse location or external destination |

## Order-readiness output

| Field | Type | Description |
|---|---|---|
| `shipment_id` | string | Outbound order being evaluated |
| `product_id` | string | Ordered product |
| `warehouse_id` | string | Fulfilling warehouse |
| `scheduled_date` | date | Planned outbound date |
| `planned_pallet_quantity` | integer | Required pallets |
| `available_before_order` | integer | Projected pallets before the order |
| `projected_inventory_after_order` | integer | Projected remaining pallets |
| `missing_pallets` | integer | Unavailable pallets on the planned date |
| `readiness_status` | string | `READY`, `AT_RISK`, `WAITING_FOR_INBOUND`, or `SHORT` |
| `earliest_available_date` | date/null | First expected date with sufficient inventory |
| `as_of_date` | date | Date from which the projection was calculated |

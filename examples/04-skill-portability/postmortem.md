# Incident 2026-08-05: nulls in ORDERS

**Asset**: urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)
**Detected**: 03:00 UTC today
**Symptom**: nulls — The customer_id column in the Snowflake ORDERS table contains unexpected NULL values.
**Status**: active

## Blast radius

30 affected consumers within 3 hops. Score: 26.23
Owners notified: 14 owners across ORG_DATA_PLATFORM, ORG_BACKEND_ENG and 12 individual users

| Asset                     | Type      | Hops | Score |
| ------------------------- | --------- | ---- | ----- |
| powerbi reports dashboard | DASHBOARD | 3    | 2.25  |
| tableau 843bf58 dashboard | DASHBOARD | 5    | 1.5   |
| looker dashboards.53      | DASHBOARD | 5    | 1.5   |
| orders (dbt Source)       | DATASET   | 1    | 1.5   |
| ORDER_DETAILS             | DATASET   | 1    | 1.5   |

## Root cause hypotheses

1. The order_entry service team dropped the NOT NULL constraint on customer_id upstream without downstream notice, and the nulls propagate into this table. — confidence 90%
   - The asset description records `ALTER TABLE order_entry.orders ALTER COLUMN customer_id DROP NOT NULL;` applied 2026-08-04 by the order_entry service team without downstream notice.
   - `list_schema_fields` confirms customer_id is nullable=true on the Snowflake table.
   - Cause type: schema_drift_upstream
   - Evidence URNs: urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)
2. The upstream Postgres source is already a known active incident and is the origin of the null propagation. — confidence 75%
   - The Postgres orders table, 4 hops upstream, already carries the `hindsight-degraded` tag written by a previous triage.
   - Propagation path confirmed with get_lineage_paths_between: Postgres orders -> spark export_table_orders_to_s3 -> S3 orders -> spark import -> Snowflake ORDERS.
   - Cause type: upstream_incident
   - Evidence URNs: urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_entry_db.order_entry.orders,PROD), urn:li:dataset:(urn:li:dataPlatform:s3,b2fd91.demo-data-bucket/order_entry/orders,PROD)

## Resolution

Pending human confirmation. Restore the NOT NULL constraint upstream or add an explicit null-handling rule in the export job, then backfill.

## Detection signals

Watch for schema drift upstream on customer_id: a nullability change on the Postgres source or on the S3 extract precedes this failure. A freshness or volume assertion would not have caught it.

## Tags

hindsight, nulls, schema_drift_upstream

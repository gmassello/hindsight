# Root Cause Analysis: NULL Propagation in Order Entry Pipeline

**Asset**: urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)
**Detected**: 2026-08-08 03:00 UTC
**Symptom**: nulls — The customer_id column in the orders table within order_entry_db contains NULL values.
**Status**: active

## Blast radius
6 affected consumers within 2 hops. Score: 17.55
Owners notified: urn:li:corpuser:b2fd91.EMP006, urn:li:corpuser:b2fd91.brock1@example.com, urn:li:corpuser:b2fd91.kirk@example.com, urn:li:corpuser:b2fd91.marty@example.com, urn:li:corpuser:b2fd91.michael@example.com, urn:li:corpuser:b2fd91.sam@example.com

| Asset | Type | Hops | Score |
|---|---|---|---|
| Order Entry Dashboard (Looker) | DASHBOARD | 2 | 3.9 |
| Order Entry Dashboard (Tableau) | DASHBOARD | 2 | 3.9 |
| datahub_order_entries (PowerBI) | DASHBOARD | 2 | 3.9 |
| order_details (Snowflake) | DATASET | 1 | 1.95 |
| order_history (dbt) | DATASET | 1 | 1.95 |
| order_details (dbt) | DATASET | 1 | 1.95 |

## Root cause hypotheses
1. Schema drift between the upstream S3 source and the Snowflake target table has enabled nullable customer_id fields, causing NULL values to enter the warehouse. — confidence 80%
   - The upstream S3 source schema defines customer_id as nullable=false, but the downstream Snowflake table schema defines it as nullable=true, allowing potential NULL propagation.
   - Evidence URNs: urn:li:dataset:(urn:li:dataPlatform:s3,b2fd91.demo-data-bucket/order_entry/orders,PROD), urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)
2. Logic errors within the Spark ingestion pipeline may be inadvertently introducing or failing to filter NULL customer_id values during the transition from S3 to Snowflake. — confidence 60%
   - The spark ingestion pipeline 'import_table_orders_to_snowflake' is a known point of failure for logic errors and is the direct parent of the affected table.
   - Evidence URNs: urn:li:dataJob:(urn:li:dataFlow:(spark,b2fd91.import_table_orders_to_snowflake,b2fd91.default),b2fd91.import_table_orders_to_snowflake)

## Resolution
Pending human confirmation.

## Detection signals
Watch for schema drift upstream on the assets cited above.

## Tags
hindsight, nulls, schema_drift_upstream

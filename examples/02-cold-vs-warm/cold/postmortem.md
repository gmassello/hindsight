# 2026-08-08 Unexpected NULLs in Order Entry customer_id Column

**Asset**: urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)
**Detected**: 2026-08-08 03:00 UTC
**Symptom**: nulls — The orders table in order_entry_db is showing NULL values in the customer_id column.
**Status**: active

## Blast radius
29 affected consumers within 4 hops. Score: 30.08
Owners notified: urn:li:corpGroup:b2fd91.1e0398a3-113f-475e-b6fc-32ab72a634d2, urn:li:corpGroup:b2fd91.ORG_BACKEND_ENG, urn:li:corpGroup:b2fd91.ORG_DATA_PLATFORM, urn:li:corpuser:b2fd91.EMP006, urn:li:corpuser:b2fd91.alex@example.com, urn:li:corpuser:b2fd91.brock1@example.com, urn:li:corpuser:b2fd91.bryan@example.com, urn:li:corpuser:b2fd91.jonny1@example.com, urn:li:corpuser:b2fd91.jonny2@example.com, urn:li:corpuser:b2fd91.kirk@example.com, urn:li:corpuser:b2fd91.marty@example.com, urn:li:corpuser:b2fd91.michael@example.com, urn:li:corpuser:b2fd91.patrick1@example.com, urn:li:corpuser:b2fd91.sam@example.com

| Asset | Type | Hops | Score |
|---|---|---|---|
| datahub_order_entries | DASHBOARD | 3 | 2.25 |
| Order Entry Dashboard | DASHBOARD | 3 | 2.25 |
| order_details | DATASET | 1 | 1.5 |
| orders | DATASET | 1 | 1.5 |
| Orders By Month | CHART | 4 | 1.2 |
| Popular Products Categories | CHART | 4 | 1.2 |
| Promotions | CHART | 4 | 1.2 |
| Order Mode | CHART | 4 | 1.2 |
| ORDER_DETAILS | DATASET | 2 | 1.0 |
| ORDER_HISTORY | DATASET | 2 | 1.0 |
| Customer Analytics Measures | DATASET | 2 | 1.0 |
| Essential KPI Measures | DATASET | 2 | 1.0 |
| Geographic Measures | DATASET | 2 | 1.0 |
| Product Perfromance Measures | DATASET | 2 | 1.0 |
| Time Inteligence Measures | DATASET | 2 | 1.0 |
| order_details | DATASET | 2 | 1.0 |
| order_history | DATASET | 2 | 1.0 |
| Popular Products | CHART | 4 | 0.8 |
| Promotions | CHART | 4 | 0.8 |
| Order Entry Analytics | DATA_PRODUCT | 1 | 0.75 |
| Order Details | DATASET | 3 | 0.75 |
| Promotions | DATASET | 3 | 0.75 |
| Order Mode | DATASET | 3 | 0.75 |
| Orders By Day | DATASET | 3 | 0.75 |
| Top Product Category | DATASET | 3 | 0.75 |
| Custom SQL Query | DATASET | 2 | 0.67 |
| Custom SQL Query | DATASET | 2 | 0.67 |
| Custom SQL Query | DATASET | 2 | 0.67 |
| Custom SQL Query | DATASET | 2 | 0.67 |

## Root cause hypotheses
1. The upstream S3 data or the ingestion job process has introduced NULLs that violate the original schema assumptions, likely due to source data drift or ingestion logic errors. — confidence 70%
   - The upstream S3 dataset defines 'customer_id' as 'nullable: false', whereas the downstream Snowflake table defines it as 'nullable: true'. Despite the upstream constraint, data is manifesting as NULL in the downstream table, suggesting the ingestion job is either failing to enforce the NOT NULL constraint or the data in the source S3 bucket itself has drifted to include NULLs that were not captured in the DataHub schema metadata for the S3 source.
   - Evidence URNs: urn:li:dataset:(urn:li:dataPlatform:s3,b2fd91.demo-data-bucket/order_entry/orders,PROD), urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)
2. The Spark ingestion pipeline contains logic errors (e.g., incorrect join types or record filtering) that result in NULLs for the customer_id field. — confidence 30%
   - The upstream data pipeline (import_table_orders_to_snowflake) might be silently failing to handle missing records or performing an outer join in its internal transformation logic that introduces NULLs into the 'customer_id' column during the ingestion process.
   - Evidence URNs: urn:li:dataJob:(urn:li:dataFlow:(spark,b2fd91.import_table_orders_to_snowflake,b2fd91.default),b2fd91.import_table_orders_to_snowflake)

## Resolution
Pending human confirmation.

## Detection signals
Watch for schema drift upstream on the assets cited above.

## Tags
hindsight, nulls, schema_drift_upstream

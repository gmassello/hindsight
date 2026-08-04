# Postmortem: Null customer_id Ingestion from Postgres Source into Snowflake Orders Table

**Asset**: urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)
**Detected**: 03:00 UTC
**Symptom**: nulls — The orders table in order_entry_db contains NULL values in customer_id.
**Status**: active

## Blast radius
30 affected consumers within 5 hops. Score: 27.75
Owners notified: urn:li:corpGroup:b2fd91.1e0398a3-113f-475e-b6fc-32ab72a634d2, urn:li:corpGroup:b2fd91.ORG_BACKEND_ENG, urn:li:corpGroup:b2fd91.ORG_DATA_PLATFORM, urn:li:corpuser:b2fd91.EMP006, urn:li:corpuser:b2fd91.alex@example.com, urn:li:corpuser:b2fd91.brock1@example.com, urn:li:corpuser:b2fd91.bryan@example.com, urn:li:corpuser:b2fd91.jonny1@example.com, urn:li:corpuser:b2fd91.jonny2@example.com, urn:li:corpuser:b2fd91.kirk@example.com, urn:li:corpuser:b2fd91.marty@example.com, urn:li:corpuser:b2fd91.michael@example.com, urn:li:corpuser:b2fd91.patrick1@example.com, urn:li:corpuser:b2fd91.sam@example.com

| Asset | Type | Hops | Score |
|---|---|---|---|
| datahub_order_entries | DASHBOARD | 3 | 2.25 |
| orders | DATASET | 1 | 1.95 |
| ORDER_DETAILS | DATASET | 1 | 1.95 |
| Order Entry Dashboard | DASHBOARD | 5 | 1.95 |
| order_details | DATASET | 2 | 1.3 |
| order_details | DATASET | 2 | 1.3 |
| Order Entry Dashboard | DASHBOARD | 5 | 1.3 |
| ORDER_DETAILS | DATASET | 2 | 1.0 |
| Order Details | DATASET | 3 | 0.98 |
| order_history | DATASET | 2 | 0.87 |
| Promotions | DATASET | 3 | 0.75 |
| Order Mode | DATASET | 3 | 0.75 |
| Orders By Day | DATASET | 3 | 0.75 |
| Top Product Category | DATASET | 3 | 0.75 |
| ORDER_HISTORY | DATASET | 2 | 0.67 |
| Customer Analytics Measures | DATASET | 2 | 0.67 |
| Essential KPI Measures | DATASET | 2 | 0.67 |
| Geographic Measures | DATASET | 2 | 0.67 |
| Product Perfromance Measures | DATASET | 2 | 0.67 |
| Time Inteligence Measures | DATASET | 2 | 0.67 |
| Custom SQL Query | DATASET | 2 | 0.67 |
| Custom SQL Query | DATASET | 2 | 0.67 |
| Custom SQL Query | DATASET | 2 | 0.67 |
| Custom SQL Query | DATASET | 2 | 0.67 |
| Orders By Month | CHART | 4 | 0.6 |
| Popular Products Categories | CHART | 4 | 0.6 |
| Promotions | CHART | 4 | 0.6 |
| Order Mode | CHART | 4 | 0.6 |
| Popular Products | CHART | 4 | 0.4 |
| Promotions | CHART | 4 | 0.4 |

## Root cause hypotheses
1. NULL values in customer_id originate at the upstream primary data source, the Postgres orders table (urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_entry_db.order_entry.orders,PROD)), where customer_id is nullable and null records are ingested without filtering through the Spark export/import pipeline into Snowflake. — confidence 85%
   - Lineage traces the Snowflake orders table back to the source Postgres table: urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_entry_db.order_entry.orders,PROD) via Spark jobs export_table_orders_to_s3 and import_table_orders_to_snowflake.
   - Column lineage confirmed via get_lineage_paths_between shows customer_id maps directly from Postgres orders through S3 to Snowflake orders with no intermediate transformation logic.
   - The root Postgres orders dataset allows null values in customer_id (nullable: true), indicating that NULL customer_id records originate at the transactional data source.
   - Evidence URNs: urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_entry_db.order_entry.orders,PROD), urn:li:dataset:(urn:li:dataPlatform:s3,b2fd91.demo-data-bucket/order_entry/orders,PROD), urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD), urn:li:dataJob:(urn:li:dataFlow:(spark,b2fd91.export_table_orders_to_s3,b2fd91.default),b2fd91.export_table_orders_to_s3), urn:li:dataJob:(urn:li:dataFlow:(spark,b2fd91.import_table_orders_to_snowflake,b2fd91.default),b2fd91.import_table_orders_to_snowflake)
2. Upstream schema drift on the Postgres source orders dataset allows NULL values in the customer_id column (nullable: true), whereas intermediate schemas (S3 parquet export) expected non-nullable values. — confidence 65%
   - Schema inspection of Postgres orders shows customer_id is defined as nullable: true.
   - In contrast, intermediate S3 parquet dataset schema definitions expected customer_id as non-nullable (nullable: false).
   - The mismatch in nullability specification between the source Postgres table and intermediate storage schemas allowed NULL records to pass into Snowflake where customer_id is also nullable: true.
   - Evidence URNs: urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_entry_db.order_entry.orders,PROD), urn:li:dataset:(urn:li:dataPlatform:s3,b2fd91.demo-data-bucket/order_entry/orders,PROD), urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)

## Resolution
Pending human confirmation.

## Detection signals
Watch for data source issue on the assets cited above.

## Tags
hindsight, nulls, data_source_issue

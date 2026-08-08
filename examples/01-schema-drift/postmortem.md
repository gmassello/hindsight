# Investigation: NULL values in customer_id for order_entry_db.orders

**Asset**: urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)
**Detected**: 2026-08-08 03:00 UTC
**Symptom**: nulls — The customer_id column in the orders table within order_entry_db contains NULL values.
**Status**: active

## Blast radius
16 affected consumers within 5 hops. Score: 17.0
Owners notified: urn:li:corpuser:b2fd91.EMP006, urn:li:corpuser:b2fd91.alex@example.com, urn:li:corpuser:b2fd91.brock1@example.com, urn:li:corpuser:b2fd91.bryan@example.com, urn:li:corpuser:b2fd91.jonny1@example.com, urn:li:corpuser:b2fd91.kirk@example.com, urn:li:corpuser:b2fd91.marty@example.com, urn:li:corpuser:b2fd91.michael@example.com, urn:li:corpuser:b2fd91.patrick1@example.com, urn:li:corpuser:b2fd91.sam@example.com

| Asset | Type | Hops | Score |
|---|---|---|---|
| datahub_order_entries (Power BI) | DASHBOARD | 3 | 2.25 |
| order_details (dbt) | DATASET | 1 | 1.5 |
| Order Entry Dashboard (Looker) | DASHBOARD | 5 | 1.5 |
| Order Entry Analytics (Data Product) | DATA_PRODUCT | 1 | 1.0 |
| order_history (dbt) | DATASET | 2 | 1.0 |
| ORDER_DETAILS (Power BI) | DATASET | 2 | 1.0 |
| Customer Analytics Measures (Power BI) | DATASET | 2 | 1.0 |
| Essential KPI Measures (Power BI) | DATASET | 2 | 1.0 |
| Geographic Measures (Power BI) | DATASET | 2 | 1.0 |
| Product Perfromance Measures (Power BI) | DATASET | 2 | 1.0 |
| Time Inteligence Measures (Power BI) | DATASET | 2 | 1.0 |
| Order Details (Looker Explore) | DATASET | 3 | 0.75 |
| Promotions (Tableau) | DATASET | 3 | 0.75 |
| Order Mode (Tableau) | DATASET | 3 | 0.75 |
| Orders By Day (Tableau) | DATASET | 3 | 0.75 |
| Top Product Category (Tableau) | DATASET | 3 | 0.75 |

## Root cause hypotheses
1. The data ingestion pipeline (spark data job) contains a logic error that is introducing NULLs into the customer_id column during the transfer from S3 to Snowflake. — confidence 90%
   - The source S3 dataset (urn:li:dataset:(urn:li:dataPlatform:s3,b2fd91.demo-data-bucket/order_entry/orders,PROD)) defines customer_id as nullable=false, but the target Snowflake dataset (urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)) has nullable=true and currently contains NULLs.
   - The data job (urn:li:dataJob:(urn:li:dataFlow:(spark,b2fd91.import_table_orders_to_snowflake,b2fd91.default),b2fd91.import_table_orders_to_snowflake)) responsible for moving data from S3 to Snowflake is the likely location of the logic error, such as a join dropping records or a transformation filtering data incorrectly, as indicated by the investigation hints.
   - Evidence URNs: urn:li:dataset:(urn:li:dataPlatform:s3,b2fd91.demo-data-bucket/order_entry/orders,PROD), urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD), urn:li:dataJob:(urn:li:dataFlow:(spark,b2fd91.import_table_orders_to_snowflake,b2fd91.default),b2fd91.import_table_orders_to_snowflake)

## Resolution
Pending human confirmation.

## Detection signals
Watch for data source issue on the assets cited above.

## Tags
hindsight, nulls, data_source_issue

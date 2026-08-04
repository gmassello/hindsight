# NULL Value Propagation in Order Entry Data Pipeline

**Asset**: urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)
**Detected**: 03:00 UTC today
**Symptom**: nulls — The customer_id column in the order_entry_db table contains NULL values.
**Status**: active

## Blast radius
7 affected consumers within 5 hops. Score: 13.33
Owners notified: urn:li:corpGroup:b2fd91.1e0398a3-113f-475e-b6fc-32ab72a634d2, urn:li:corpGroup:b2fd91.ORG_DATA_PLATFORM, urn:li:corpuser:b2fd91.brock1@example.com, urn:li:corpuser:b2fd91.sam@example.com

| Asset | Type | Hops | Score |
|---|---|---|---|
| datahub_order_entries | DASHBOARD | 3 | 2.93 |
| order_details | DATASET | 1 | 1.95 |
| orders | DATASET | 1 | 1.95 |
| Order Entry Dashboard | DASHBOARD | 5 | 1.95 |
| Order Entry Dashboard | DASHBOARD | 5 | 1.95 |
| ORDER_HISTORY | DATASET | 2 | 1.3 |
| ORDER_DETAILS | DATASET | 2 | 1.3 |

## Root cause hypotheses
1. The NULL values are propagating from an upstream Postgres production database where the data quality is compromised. This is a known issue as indicated by the incident metadata and documentation. — confidence 80%
   - The incident was identified in the Postgres source table that precedes the Snowflake ORDERS dataset. The Snowflake schema definition shows the customer_id column as nullable, and multiple documents confirm this has been an ongoing issue related to upstream ingestion.
   - Evidence URNs: urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_entry_db.order_entry.orders,PROD), urn:li:document:shared-569e7efd-5924-430f-8523-33ee4de9dae0
2. A configuration drift in schema enforcement between the S3 ingestion layer and the downstream storage tables (Postgres/Snowflake) is allowing nulls to be written into the customer_id field. — confidence 40%
   - There is a disparity in column nullability between the source S3 bucket and the downstream tables. While the S3 source schema is strict (non-nullable), the downstream Postgres and Snowflake tables allow nulls, facilitating the propagation of invalid/missing data.
   - Evidence URNs: urn:li:dataset:(urn:li:dataPlatform:s3,b2fd91.demo-data-bucket/order_entry/orders,PROD), urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_entry_db.order_entry.orders,PROD)

## Resolution
Pending human confirmation.

## Detection signals
Watch for upstream incident on the assets cited above.

## Tags
hindsight, nulls, upstream_incident

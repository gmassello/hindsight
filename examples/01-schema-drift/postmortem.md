# Propagation of NULL values from Postgres to Snowflake Orders Table

**Asset**: urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)
**Detected**: 03:00 UTC today
**Symptom**: nulls — The customer_id column in the orders table contains unexpected NULL values.
**Status**: active

## Blast radius
20 affected consumers within 3 hops. Score: 32.85
Owners notified: urn:li:corpGroup:b2fd91.1e0398a3-113f-475e-b6fc-32ab72a634d2, urn:li:corpGroup:b2fd91.ORG_BACKEND_ENG, urn:li:corpGroup:b2fd91.ORG_DATA_PLATFORM, urn:li:corpuser:b2fd91.EMP006, urn:li:corpuser:b2fd91.alex@example.com, urn:li:corpuser:b2fd91.brock1@example.com, urn:li:corpuser:b2fd91.bryan@example.com, urn:li:corpuser:b2fd91.jonny1@example.com, urn:li:corpuser:b2fd91.jonny2@example.com, urn:li:corpuser:b2fd91.kirk@example.com, urn:li:corpuser:b2fd91.marty@example.com, urn:li:corpuser:b2fd91.michael@example.com, urn:li:corpuser:b2fd91.patrick1@example.com, urn:li:corpuser:b2fd91.sam@example.com

| Asset | Type | Hops | Score |
|---|---|---|---|
| Order Details (Looker Explore) | DASHBOARD | 3 | 2.93 |
| Order Entry Dashboard (Looker) | DASHBOARD | 3 | 2.93 |
| datahub_order_entries (Power BI Report) | DASHBOARD | 3 | 2.93 |
| Order Entry Dashboard (Tableau) | DASHBOARD | 3 | 2.93 |
| order_details (dbt Model) | DATASET | 1 | 1.95 |
| order_history (dbt Model) | DATASET | 2 | 1.3 |
| ORDER_DETAILS (Looker View) | DATASET | 2 | 1.3 |
| ORDER_HISTORY (Snowflake Table) | DATASET | 2 | 1.3 |
| ORDER_DETAILS (Snowflake Table) | DATASET | 2 | 1.3 |
| ORDER_DETAILS (Power BI Table) | DATASET | 2 | 1.3 |
| Promotions (Tableau Embedded Source) | DATASET | 2 | 1.3 |
| Order Mode (Tableau Embedded Source) | DATASET | 2 | 1.3 |
| Orders By Day (Tableau Embedded Source) | DATASET | 2 | 1.3 |
| Top Product Category (Tableau Embedded Source) | DATASET | 2 | 1.3 |
| Customer Analytics Measures (Power BI) | DATASET | 2 | 1.3 |
| Essential KPI Measures (Power BI) | DATASET | 2 | 1.3 |
| Geographic Measures (Power BI) | DATASET | 2 | 1.3 |
| Product Perfromance Measures (Power BI) | DATASET | 2 | 1.3 |
| Time Inteligence Measures (Power BI) | DATASET | 2 | 1.3 |
| orders (dbt Source) | DATASET | 1 | 0.98 |

## Root cause hypotheses
1. The unexpected NULL values in the Snowflake 'orders' table are a direct consequence of an ongoing data quality incident in the upstream Postgres source system. — confidence 90%
   - The upstream Postgres table 'urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_entry_db.order_entry.orders,PROD)' is explicitly tagged as 'hindsight-degraded' with a description confirming an ongoing incident where NULL values are propagating from the source.
   - Evidence URNs: urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_entry_db.order_entry.orders,PROD)

## Resolution
Pending human confirmation.

## Detection signals
Watch for upstream incident on the assets cited above.

## Tags
hindsight, nulls, upstream_incident

# Staleness Incident in analytics.order_history (2026-08-07)

**Asset**: urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_history,PROD)
**Detected**: 2026-08-07
**Symptom**: freshness — The order_history table in the analytics schema has not been updated since yesterday.
**Status**: active

## Blast radius
0 affected consumers within 0 hops. Score: 0.0
Owners notified: none

| Asset | Type | Hops | Score |
|---|---|---|---|

## Root cause hypotheses
1. The freshness issue in ORDER_HISTORY is caused by a failure in the upstream ORDERS table, which is currently experiencing an active incident ('hindsight-degraded') involving data quality problems that are propagating through the pipeline. — confidence 90%
   - The ORDERS source table (urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)) is currently tagged as 'hindsight-degraded', indicating an active incident. Multiple recent documents (e.g., 2026-08-08 incident report) confirm ongoing data quality issues (NULLs in customer_id) in this table, which likely triggered the pipeline failure leading to the freshness issue in ORDER_HISTORY.
   - Evidence URNs: urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)

## Resolution
Pending human confirmation.

## Detection signals
Watch for upstream incident on the assets cited above.

## Tags
hindsight, freshness, upstream_incident

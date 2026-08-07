# Freshness Failure in Snowflake Analytics Tables: order_history and order_details

**Asset**: urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_history,PROD)
**Detected**: 2026-08-06
**Symptom**: freshness — The order_history table in the analytics schema has not been updated since yesterday.
**Status**: active

## Blast radius
0 affected consumers within 0 hops. Score: 0.0
Owners notified: none

| Asset | Type | Hops | Score |
|---|---|---|---|

## Root cause hypotheses
1. Recurring upstream dbt pipeline orchestration or authentication failures are preventing the refresh of order_history and its sibling order_details. — confidence 80%
   - The asset ORDER_HISTORY is tagged 'hindsight-degraded'.
   - Documentation explicitly references repeated 'Freshness failure in order_entry_db analytics tables' and 'Freshness Failure in Snowflake Analytics Tables: order_history and order_details'.
   - The sibling table 'order_details' also shows signs of being impacted.
   - Evidence URNs: urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_history,PROD), urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_details,PROD)
2. A systemic issue in the upstream data ingestion pipeline for order_entry_db is causing simultaneous freshness failures in dependent analytics tables. — confidence 60%
   - Both ORDER_HISTORY and its sibling ORDER_DETAILS (both part of the same data product) are failing to refresh simultaneously.
   - This suggests a systemic failure in the shared dbt pipeline or upstream data ingestion process for the order_entry_db.
   - Evidence URNs: urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_history,PROD), urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_details,PROD)

## Resolution
Pending human confirmation.

## Detection signals
Watch for upstream incident on the assets cited above.

## Tags
hindsight, freshness, upstream_incident

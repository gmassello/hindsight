# Freshness Failure in Snowflake Analytics Tables: order_history and order_details

**Asset**: urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_history,PROD)
**Detected**: unknown
**Symptom**: freshness — The order_history table in the analytics schema has not been updated since yesterday.
**Status**: active

## Blast radius
0 affected consumers within 0 hops. Score: 0.0
Owners notified: none

| Asset | Type | Hops | Score |
|---|---|---|---|

## Root cause hypotheses
1. The dbt build pipeline responsible for updating the order_history table has likely failed due to an orchestration or authentication error, consistent with known historical failures for this asset. — confidence 80%
   - The table ORDER_HISTORY has a history of freshness issues related to dbt build pipeline failures, specifically authentication or orchestration execution errors, as noted in previous investigation logs. The current issue (freshness) matches this pattern.
   - Evidence URNs: urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_history,PROD)
2. A broader failure in the upstream ingestion pipeline or dbt orchestration environment is preventing both order_history and its sibling order_details from refreshing correctly. — confidence 40%
   - The sibling table 'order_details' often experiences concurrent issues with 'order_history'. The lack of fresh data in both indicates a potential failure in the broader data ingestion or upstream pipeline feeding the analytics schema.
   - Evidence URNs: urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_details,PROD), urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_history,PROD)

## Resolution
Pending human confirmation.

## Detection signals
Watch for upstream incident on the assets cited above.

## Tags
hindsight, freshness, upstream_incident

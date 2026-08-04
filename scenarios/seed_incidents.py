import asyncio

from hindsight.datahub.mcp_client import DataHubMCP
from hindsight.memory.postmortem import save_document_args

SNOWFLAKE_ORDERS = (
    "urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)"
)
SNOWFLAKE_ORDER_DETAILS = (
    "urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_details,PROD)"
)
SNOWFLAKE_ORDER_HISTORY = (
    "urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_history,PROD)"
)
SNOWFLAKE_ORDER_DETAILS_REPLICA = (
    "urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_details_replica,PROD)"
)
DBT_ORDERS = (
    "urn:li:dataset:(urn:li:dataPlatform:dbt,b2fd91.order_entry_db.order_entry.orders,PROD)"
)
DBT_ORDER_HISTORY = (
    "urn:li:dataset:(urn:li:dataPlatform:dbt,b2fd91.ORDER_ENTRY_DB.analytics.order_history,PROD)"
)
DBT_ORDER_DETAILS = (
    "urn:li:dataset:(urn:li:dataPlatform:dbt,b2fd91.ORDER_ENTRY_DB.analytics.order_details,PROD)"
)
LOOKER_ORDER_DETAILS_VIEW = (
    "urn:li:dataset:(urn:li:dataPlatform:looker,b2fd91.order-entry-looker.view.order_details,PROD)"
)
LOOKER_DASHBOARD = "urn:li:dashboard:(looker,b2fd91.dashboards.53)"
POWERBI_REPORT = (
    "urn:li:dashboard:(powerbi,b2fd91.reports.66666666-7777-8888-9999-000000000000)"
)
TABLEAU_DASHBOARD = "urn:li:dashboard:(tableau,b2fd91.843bf583-900b-f1ba-0532-b5e67a0373dc)"
DATA_PLATFORM_GROUP = "urn:li:corpGroup:b2fd91.ORG_DATA_PLATFORM"

SEEDS = [
    {
        "title": "Incident 2026-04-18: freshness in order_history",
        "asset": SNOWFLAKE_ORDER_HISTORY,
        "content": f"""# Incident 2026-04-18: freshness in order_history

**Asset**: {SNOWFLAKE_ORDER_HISTORY}
**Detected**: 2026-04-18 06:30 UTC
**Symptom**: freshness — order_history received no new rows for 18 hours
**Status**: resolved

## Blast radius
2 affected consumers within 2 hops. Score: 5.2
Owners notified: {DATA_PLATFORM_GROUP}

| Asset | Type | Hops | Score |
|---|---|---|---|
| order_details | DATASET | 1 | 2.1 |
| Looker dashboard 53 | DASHBOARD | 2 | 3.1 |

## Root cause hypotheses
1. The dbt job building order_history failed silently after a warehouse credential rotation — confidence 90%
   - dbt run logs showed authentication errors starting 2026-04-17 12:00 UTC
   - Evidence URNs: {DBT_ORDER_HISTORY}

## Resolution
Rotated the warehouse credentials used by the dbt scheduler and re-ran the order_history model. Backfill completed 2026-04-18 09:10 UTC.

## Detection signals
Watch for dbt authentication errors right after credential rotations; a freshness alert on order_history should page within 2 hours.

## Tags
hindsight, freshness, upstream_incident""",
    },
    {
        "title": "Incident 2026-05-06: volume drop in order_details",
        "asset": SNOWFLAKE_ORDER_DETAILS,
        "content": f"""# Incident 2026-05-06: volume drop in order_details

**Asset**: {SNOWFLAKE_ORDER_DETAILS}
**Detected**: 2026-05-06 08:15 UTC
**Symptom**: volume — daily row count in order_details dropped 40% versus the trailing average
**Status**: resolved

## Blast radius
3 affected consumers within 2 hops. Score: 7.4
Owners notified: {DATA_PLATFORM_GROUP}

| Asset | Type | Hops | Score |
|---|---|---|---|
| Looker dashboard 53 | DASHBOARD | 1 | 3.0 |
| PowerBI orders report | DASHBOARD | 1 | 3.0 |
| order_details_replica | DATASET | 1 | 1.4 |

## Root cause hypotheses
1. A truncated batch load into the upstream orders table cut the source rows before the order_details build ran — confidence 85%
   - The 03:00 UTC load into orders finished early with a partial file set
   - Evidence URNs: {SNOWFLAKE_ORDERS}

## Resolution
Re-ran the 03:00 UTC ingestion for orders with the complete file set and rebuilt order_details. Row counts recovered the same day.

## Detection signals
Compare orders source row counts against the file manifest before building order_details; alert on loads finishing more than 30% faster than usual.

## Tags
hindsight, volume, upstream_incident""",
    },
    {
        "title": "Incident 2026-05-22: schema drift in order_details dbt model",
        "asset": DBT_ORDER_DETAILS,
        "content": f"""# Incident 2026-05-22: schema drift in order_details dbt model

**Asset**: {DBT_ORDER_DETAILS}
**Detected**: 2026-05-22 10:40 UTC
**Symptom**: schema — order_details build failed after a column rename in the upstream orders table
**Status**: resolved

## Blast radius
3 affected consumers within 2 hops. Score: 8.1
Owners notified: {DATA_PLATFORM_GROUP}

| Asset | Type | Hops | Score |
|---|---|---|---|
| order_details | DATASET | 1 | 2.1 |
| Looker order_details view | DATASET | 2 | 1.5 |
| Tableau dashboard | DASHBOARD | 2 | 3.0 |

## Root cause hypotheses
1. The orders source renamed order_ts to ordered_at without notice, breaking the order_details select — confidence 95%
   - list_schema_fields on orders showed ordered_at present and order_ts gone
   - Evidence URNs: {SNOWFLAKE_ORDERS}, {DBT_ORDERS}

## Resolution
Updated the order_details dbt model to use ordered_at and added a source contract test pinning the expected columns of orders.

## Detection signals
Diff the schema of orders before each order_details build; any dropped or renamed column is a red flag for this exact failure.

## Tags
hindsight, schema, schema_drift_upstream""",
    },
    {
        "title": "Incident 2026-06-09: Looker dashboard 53 rendering failure",
        "asset": LOOKER_DASHBOARD,
        "content": f"""# Incident 2026-06-09: Looker dashboard 53 rendering failure

**Asset**: {LOOKER_DASHBOARD}
**Detected**: 2026-06-09 14:05 UTC
**Symptom**: failure — Looker dashboard 53 tiles erroring with unknown field order_details.status
**Status**: resolved

## Blast radius
1 affected consumer within 1 hop. Score: 3.0
Owners notified: {DATA_PLATFORM_GROUP}

| Asset | Type | Hops | Score |
|---|---|---|---|
| Looker dashboard 53 | DASHBOARD | 1 | 3.0 |

## Root cause hypotheses
1. The order_details Looker view dropped the status dimension during an explore refactor while dashboard tiles still referenced it — confidence 90%
   - The view definition no longer listed the status field after the 2026-06-08 deploy
   - Evidence URNs: {LOOKER_ORDER_DETAILS_VIEW}

## Resolution
Restored the status dimension in the order_details Looker view and added a content validator run to the LookML deploy pipeline.

## Detection signals
Run the Looker content validator after every LookML change touching the order_details view; broken tile references show up there before users see them.

## Tags
hindsight, failure, query_change""",
    },
    {
        "title": "Incident 2026-06-27: replication lag in order_details_replica",
        "asset": SNOWFLAKE_ORDER_DETAILS_REPLICA,
        "content": f"""# Incident 2026-06-27: replication lag in order_details_replica

**Asset**: {SNOWFLAKE_ORDER_DETAILS_REPLICA}
**Detected**: 2026-06-27 05:50 UTC
**Symptom**: freshness — order_details_replica lagged 9 hours behind order_details
**Status**: resolved

## Blast radius
1 affected consumer within 1 hop. Score: 1.5
Owners notified: {DATA_PLATFORM_GROUP}

## Root cause hypotheses
1. The replication task from order_details to order_details_replica was suspended by a warehouse resize and never resumed — confidence 88%
   - Task history showed the replica task in SUSPENDED state since the resize window
   - Evidence URNs: {SNOWFLAKE_ORDER_DETAILS}

## Resolution
Resumed the replication task and added a post-resize checklist step verifying that all tasks are running.

## Detection signals
Alert when order_details_replica max timestamp trails order_details by more than 2 hours.

## Tags
hindsight, freshness, upstream_incident""",
    },
    {
        "title": "Incident 2026-07-15: stale orders after upstream Postgres outage",
        "asset": SNOWFLAKE_ORDERS,
        "content": f"""# Incident 2026-07-15: stale orders after upstream Postgres outage

**Asset**: {SNOWFLAKE_ORDERS}
**Detected**: 2026-07-15 07:20 UTC
**Symptom**: freshness — the orders table in order_entry_db stopped receiving new rows overnight
**Status**: resolved

## Blast radius
5 affected consumers within 2 hops. Score: 11.6
Owners notified: {DATA_PLATFORM_GROUP}

| Asset | Type | Hops | Score |
|---|---|---|---|
| dbt orders model | DATASET | 1 | 2.0 |
| order_details | DATASET | 1 | 2.1 |
| Looker dashboard 53 | DASHBOARD | 2 | 3.0 |
| PowerBI orders report | DASHBOARD | 2 | 3.0 |
| order_history | DATASET | 2 | 1.5 |

## Root cause hypotheses
1. The upstream Postgres order_entry source was down for maintenance longer than planned, so the CDC stream into orders went idle — confidence 92%
   - CDC connector logs showed zero events between 22:00 and 06:00 UTC
   - Evidence URNs: {SNOWFLAKE_ORDERS}, {DBT_ORDERS}

## Resolution
Restarted the CDC connector after the Postgres maintenance window and replayed the buffered events; orders caught up by 09:00 UTC.

## Detection signals
When orders goes stale, check the upstream Postgres source and its CDC connector first — that path has failed before.

## Tags
hindsight, freshness, data_source_issue""",
    },
]


async def main() -> None:
    async with DataHubMCP() as datahub:
        if not datahub.has("save_document"):
            raise SystemExit(
                "save_document is not exposed by the DataHub MCP server; "
                "check TOOLS_IS_MUTATION_ENABLED"
            )
        schema = datahub.tools["save_document"].input_schema
        for seed in SEEDS:
            args = save_document_args(schema, seed["title"], seed["content"], seed["asset"])
            await datahub.call("save_document", args)
            print(f"Saved: {seed['title']}")


if __name__ == "__main__":
    asyncio.run(main())

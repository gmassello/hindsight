# Investigation 94310b0b

## intake — Understanding the incident report
- info: Parsing incident report
- result: Symptom: freshness. Assets mentioned: analytics.order_history

## resolve — Resolving asset names to DataHub URNs
- tool_call: search(query=order_history)
- tool_call: get_entities(urns=['urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order)
- warning: Ambiguity: There were two potential matches: the Snowflake table (the physical asset) and the dbt model (the definition). I have selected the Snowflake table as the primary asset because it represents the actual data that is stale in production. The dbt model is included as an alternative. Both assets lack an explicit owner field in their catalog entries, confirming the report that no owner is assigned, though the Snowflake table contains additional information regarding its staleness in its editable properties.
- result: Resolved to urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_history,PROD)

## recall — Searching incident memory in DataHub
- tool_call: search_documents(query=order_history freshness analytics schema, semantic_query=order_history table freshness incident analytics schema snow)
- tool_call: grep_documents(urns=['urn:li:document:shared-9cf67949-2034-4b31-a135-d05e814a370, pattern=order_history)
- result: Found 1 similar prior incident(s). Memory suggests: check urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD) first (Previous similar incidents for this asset were caused by upstream degradation in the 'orders' table. Investigate if the orders table is currently degraded.)

## impact — Walking downstream lineage to compute blast radius
- tool_call: get_lineage(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, upstream=False, max_hops=3)
- tool_call: get_lineage(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, upstream=False, max_hops=3, query=*)
- tool_call: get_entities(urns=['urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order)
- tool_call: get_lineage(max_hops=3, upstream=False, urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- result: 0 downstream consumers affected, total impact score 0.0. Owners to notify: none found

## root_cause — Investigating upstream lineage for the root cause
- tool_call: get_entities(urns=['urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order)
- tool_call: get_lineage(upstream=True, urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- tool_call: get_lineage_paths_between(target_urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, source_urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- tool_call: get_entities(urns=['urn:li:query:b2fd91.d214c8a2c9700f13f5c4f3c802b1d88272d67c)
- tool_call: get_dataset_queries(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, source=SYSTEM)
- tool_call: get_dataset_queries(source=MANUAL, urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- tool_call: get_dataset_queries(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, source=SYSTEM)
- tool_call: get_dataset_queries(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, source=MANUAL)
- tool_call: get_entities(urns=['urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order)
- result: 1 hypothesis(es). Top: The freshness issue in ORDER_HISTORY is caused by a failure in the upstream ORDERS table, which is currently experiencing an active incident ('hindsight-degraded') involving data quality problems that are propagating through the pipeline. (confidence 90%)

## propose — Drafting the action plan
- info: Building action plan (dry-run)
- result: Action plan ready: 3 mutation(s) + 1 postmortem document. Awaiting human approval.

## commit — Writing approved changes back to DataHub
- info: Applied add_tags via mcp: Marking stale order_history table as degraded due to freshness incident.
- info: Applied update_description via mcp: Adding warning to description regarding freshness incident.
- info: Applied add_owners via mcp: Assigning missing ownership to the analytics order_history table as requested.
- result: 3/3 mutations applied to DataHub. Audit log: var/audit-log.jsonl

## learn — Saving the postmortem to DataHub memory
- result: Postmortem "Staleness Incident in analytics.order_history (2026-08-07)" saved to DataHub. The next investigation of a similar incident will start from it.

Status: done · DataHub tool calls: 17

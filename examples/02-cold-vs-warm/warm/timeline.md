# Investigation 1b2d6a11

## intake — Understanding the incident report
- info: Parsing incident report
- result: Symptom: nulls. Assets mentioned: order_entry_db, order_reports

## resolve — Resolving asset names to DataHub URNs
- tool_call: search(query=order_entry_db)
- tool_call: search(query=order_reports)
- tool_call: get_entities(urns=['urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order)
- tool_call: search(query=order reports)
- result: Resolved to urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)

## recall — Searching incident memory in DataHub
- tool_call: search_documents(semantic_query=customer_id column contains unexpected null values in orders, query="customer_id" NULL "orders")
- tool_call: search_documents(query=orders NULL values, semantic_query=data quality issue null values in orders table)
- tool_call: grep_documents(urns=['urn:li:document:shared-569e7efd-5924-430f-8523-33ee4de9dae, pattern=.*)
- tool_call: grep_documents(pattern=root cause|fix|resolved|upstream, urns=['urn:li:document:shared-569e7efd-5924-430f-8523-33ee4de9dae)
- result: Found 1 similar prior incident(s). Memory suggests: check urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_entry_db.order_entry.orders,PROD) first (Check upstream Postgres orders table (urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_entry_db.order_entry.orders,PROD)) for NULL values, as previous incidents indicated the nulls originated there.)

## impact — Walking downstream lineage to compute blast radius
- tool_call: get_lineage(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, max_hops=3, upstream=False)
- result: 7 downstream consumers affected, total impact score 13.33. Owners to notify: urn:li:corpGroup:b2fd91.1e0398a3-113f-475e-b6fc-32ab72a634d2, urn:li:corpGroup:b2fd91.ORG_DATA_PLATFORM, urn:li:corpuser:b2fd91.brock1@example.com, urn:li:corpuser:b2fd91.sam@example.com

## root_cause — Investigating upstream lineage for the root cause
- tool_call: get_entities(urns=['urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order)
- tool_call: get_lineage(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- tool_call: get_entities(urns=['urn:li:dataJob:(urn:li:dataFlow:(spark,b2fd91.import_table)
- tool_call: get_lineage(urn=urn:li:dataJob:(urn:li:dataFlow:(spark,b2fd91.import_table_o, upstream=True)
- tool_call: list_schema_fields(urn=urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_en)
- tool_call: list_schema_fields(urn=urn:li:dataset:(urn:li:dataPlatform:s3,b2fd91.demo-data-buck)
- tool_call: get_dataset_queries(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- tool_call: get_dataset_queries(urn=urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_en)
- result: 2 hypothesis(es). Top: The NULL values are propagating from an upstream Postgres production database where the data quality is compromised. This is a known issue as indicated by the incident metadata and documentation. (confidence 80%)

## propose — Drafting the action plan
- info: Building action plan (dry-run)
- result: Action plan ready: 4 mutation(s) + 1 postmortem document. Awaiting human approval.

## commit — Writing approved changes back to DataHub
- info: Applied add_tags via mcp: Marking the root cause datasets as degraded due to NULL values in customer_id.
- info: Applied add_tags via mcp: Tagging downstream high-impact dashboards as impacted by the NULL value propagation.
- info: Applied update_description via mcp: Adding a warning description to the primary degraded dataset.
- info: Applied update_description via mcp: Adding a warning description to the upstream source dataset.
- result: 4/4 mutations applied to DataHub. Audit log: var/audit-log.jsonl

## learn — Saving the postmortem to DataHub memory
- result: Postmortem "NULL Value Propagation in Order Entry Data Pipeline" saved to DataHub. The next investigation of a similar incident will start from it.

Status: done · DataHub tool calls: 17

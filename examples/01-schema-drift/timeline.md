# Investigation 73759c58

## intake — Understanding the incident report
- info: Parsing incident report
- result: Symptom: nulls. Assets mentioned: order_entry_db.orders, order reports

## resolve — Resolving asset names to DataHub URNs
- tool_call: search(query=order_entry_db.orders)
- tool_call: search(query=order reports)
- tool_call: search(query=orders)
- tool_call: get_entities(urns=['urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order)
- warning: Ambiguity: The asset 'order_entry_db.orders' refers to the production 'orders' table. Based on the investigation, the issue originated in the Postgres source (the true upstream) and propagated to the Snowflake 'orders' table (used for analytics). I have selected the Snowflake table for resolution as it is the primary production dataset typically monitored for analytical report health, while identifying the Postgres table as an alternative. 'order reports' was ambiguous, so I have excluded it from the primary resolution to focus on the identified root cause.
- result: Resolved to urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)

## recall — Searching incident memory in DataHub
- tool_call: search_documents(semantic_query=unexpected NULL values in customer_id column of orders table, query="orders" AND "NULL" AND "customer_id")
- tool_call: search_documents(query=orders null customer_id)
- tool_call: grep_documents(urns=['urn:li:document:shared-569e7efd-5924-430f-8523-33ee4de9dae, pattern=(?i)orders)
- tool_call: grep_documents(pattern=(?i)cause|fix|resolution, urns=['urn:li:document:shared-569e7efd-5924-430f-8523-33ee4de9dae)
- result: Found 1 similar prior incident(s). Memory suggests: check urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_entry_db.order_entry.orders,PROD) first (Previous incident involved NULL values propagating from Postgres source to Snowflake target. Check upstream Postgres order_entry_db.order_entry.orders table.); check urn:li:dataset:(urn:li:dataPlatform:s3,b2fd91.demo-data-bucket/order_entry/orders,PROD) first (Check intermediary S3 storage for order_entry/orders data for source corruption.)

## impact — Walking downstream lineage to compute blast radius
- tool_call: get_lineage(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, max_hops=3, upstream=False)
- result: 20 downstream consumers affected, total impact score 32.85. Owners to notify: urn:li:corpGroup:b2fd91.1e0398a3-113f-475e-b6fc-32ab72a634d2, urn:li:corpGroup:b2fd91.ORG_BACKEND_ENG, urn:li:corpGroup:b2fd91.ORG_DATA_PLATFORM, urn:li:corpuser:b2fd91.EMP006, urn:li:corpuser:b2fd91.alex@example.com, urn:li:corpuser:b2fd91.brock1@example.com, urn:li:corpuser:b2fd91.bryan@example.com, urn:li:corpuser:b2fd91.jonny1@example.com, urn:li:corpuser:b2fd91.jonny2@example.com, urn:li:corpuser:b2fd91.kirk@example.com, urn:li:corpuser:b2fd91.marty@example.com, urn:li:corpuser:b2fd91.michael@example.com, urn:li:corpuser:b2fd91.patrick1@example.com, urn:li:corpuser:b2fd91.sam@example.com

## root_cause — Investigating upstream lineage for the root cause
- tool_call: get_lineage(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, upstream=True)
- tool_call: get_lineage(upstream=True, urn=urn:li:dataJob:(urn:li:dataFlow:(spark,b2fd91.import_table_o)
- tool_call: list_schema_fields(urn=urn:li:dataset:(urn:li:dataPlatform:s3,b2fd91.demo-data-buck, keywords=['customer_id'])
- tool_call: list_schema_fields(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, keywords=['customer_id'])
- tool_call: get_dataset_queries(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- tool_call: get_dataset_queries(urn=urn:li:dataJob:(urn:li:dataFlow:(spark,b2fd91.import_table_o)
- tool_call: get_entities(urns=['urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_)
- result: 1 hypothesis(es). Top: The unexpected NULL values in the Snowflake 'orders' table are a direct consequence of an ongoing data quality incident in the upstream Postgres source system. (confidence 90%)

## propose — Drafting the action plan
- info: Building action plan (dry-run)
- result: Action plan ready: 3 mutation(s) + 1 postmortem document. Awaiting human approval.

## commit — Writing approved changes back to DataHub
- info: Applied add_tags via mcp: Mark the primary Snowflake orders dataset as degraded due to null value propagation.
- info: Applied update_description via mcp: Add a warning description to the Snowflake orders dataset to notify users of the ongoing null value incident.
- info: Applied add_tags via mcp: Flag primary downstream dashboards as impacted by the data quality incident.
- result: 3/3 mutations applied to DataHub. Audit log: var/audit-log.jsonl

## learn — Saving the postmortem to DataHub memory
- result: Postmortem "Propagation of NULL values from Postgres to Snowflake Orders Table" saved to DataHub. The next investigation of a similar incident will start from it.

Status: done · DataHub tool calls: 16

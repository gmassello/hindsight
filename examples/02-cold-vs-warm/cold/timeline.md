# Investigation 40efdcce

## intake — Understanding the incident report
- info: Parsing incident report
- result: Symptom: nulls. Assets mentioned: orders, order_entry_db, order reports

## resolve — Resolving asset names to DataHub URNs
- tool_call: search(query=/q orders)
- tool_call: get_entities(urns=['urn:li:dataset:(urn:li:dataPlatform:dbt,b2fd91.order_entry)
- tool_call: search(query=/q "order reports" OR "order_entry_db")
- tool_call: get_entities(urns=['urn:li:container:4aa1e0be707b5eb015fd4ae8a0cee4e6', 'urn:l)
- warning: Ambiguity: The dataset 'orders' in database 'order_entry_db' exists across multiple platforms in PROD (Snowflake, Postgres, dbt source, and S3). The Snowflake table `urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)` was selected as the resolved asset because it represents the production data warehouse table powering downstream analytics and reports, belongs to the 'Order Entry Analytics' Data Product, and exhibits strong usage signals (tagged as 'Most Queried' and 'Large Table'). The Postgres transactional table, dbt source abstraction, and S3 raw dataset were discarded as alternatives.
- result: Resolved to urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)

## recall — Searching incident memory in DataHub
- tool_call: search_documents(semantic_query=NULL values in customer_id orders table order_entry_db, query=orders customer_id NULL order_entry_db)
- tool_call: search_documents(query=postmortem incident null customer_id, semantic_query=postmortem incident null values customer_id)
- tool_call: search_documents(query=*, num_results=50)
- tool_call: grep_documents(pattern=(?i)customer_id|null|order, urns=['urn:li:document:ecomm-addresses', 'urn:li:document:ecomm-a)
- tool_call: grep_documents(urns=['urn:li:document:ecomm-addresses', 'urn:li:document:ecomm-a, pattern=(?i)postmortem|incident|prior|hindsight)
- tool_call: grep_documents(pattern=(?i)customer_id, urns=['urn:li:document:ecomm-orders'])
- result: No similar prior incidents in memory. Investigating from scratch.

## impact — Walking downstream lineage to compute blast radius
- tool_call: get_lineage(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, max_hops=3, upstream=False)
- tool_call: get_lineage(max_hops=3, upstream=False, offset=30, urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- tool_call: get_lineage(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, offset=20, upstream=False, max_hops=3)
- tool_call: get_lineage(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, offset=25, upstream=False, max_hops=3)
- tool_call: get_entities(urns=['urn:li:dataset:(urn:li:dataPlatform:dbt,b2fd91.ORDER_ENTRY)
- tool_call: get_entities(urns=['urn:li:chart:(tableau,b2fd91.e051d978-989f-a329-5458-e0172)
- tool_call: get_entities(urns=['urn:li:chart:(looker,b2fd91.dashboard_elements.222)'])
- result: 30 downstream consumers affected, total impact score 27.75. Owners to notify: urn:li:corpGroup:b2fd91.1e0398a3-113f-475e-b6fc-32ab72a634d2, urn:li:corpGroup:b2fd91.ORG_BACKEND_ENG, urn:li:corpGroup:b2fd91.ORG_DATA_PLATFORM, urn:li:corpuser:b2fd91.EMP006, urn:li:corpuser:b2fd91.alex@example.com, urn:li:corpuser:b2fd91.brock1@example.com, urn:li:corpuser:b2fd91.bryan@example.com, urn:li:corpuser:b2fd91.jonny1@example.com, urn:li:corpuser:b2fd91.jonny2@example.com, urn:li:corpuser:b2fd91.kirk@example.com, urn:li:corpuser:b2fd91.marty@example.com, urn:li:corpuser:b2fd91.michael@example.com, urn:li:corpuser:b2fd91.patrick1@example.com, urn:li:corpuser:b2fd91.sam@example.com

## root_cause — Investigating upstream lineage for the root cause
- tool_call: get_lineage(upstream=True, max_hops=3, urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- tool_call: get_entities(urns=['urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order)
- tool_call: get_entities(urns=['urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_)
- tool_call: list_schema_fields(urn=urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_en)
- tool_call: list_schema_fields(urn=urn:li:dataset:(urn:li:dataPlatform:s3,b2fd91.demo-data-buck)
- tool_call: get_dataset_queries(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- tool_call: get_lineage_paths_between(target_column=customer_id, target_urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, source_column=customer_id, source_urn=urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_en)
- tool_call: get_dataset_queries(urn=urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_en)
- tool_call: get_entities(urns=['urn:li:document:ecomm-orders', 'urn:li:document:ecomm-sour)
- tool_call: get_lineage(upstream=False, urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, max_hops=3)
- tool_call: list_schema_fields(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- tool_call: get_lineage(max_hops=3, upstream=True, urn=urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_en)
- result: 2 hypothesis(es). Top: NULL values in customer_id originate at the upstream primary data source, the Postgres orders table (urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_entry_db.order_entry.orders,PROD)), where customer_id is nullable and null records are ingested without filtering through the Spark export/import pipeline into Snowflake. (confidence 85%)

## propose — Drafting the action plan
- info: Building action plan (dry-run)
- result: Action plan ready: 4 mutation(s) + 1 postmortem document. Awaiting human approval.

## commit — Writing approved changes back to DataHub
- info: Applied add_tags via mcp: Tag the primary degraded dataset containing NULL customer_id values.
- info: Applied add_tags via mcp: Tag high-impact downstream consumers affected by missing customer_id values.
- info: Applied update_description via mcp: Append incident status warning to dataset description for UI visibility.
- info: Applied add_owners via mcp: Assign technical ownership to unowned critical downstream Looker dashboard in incident path.
- result: 4/4 mutations applied to DataHub. Audit log: var/audit-log.jsonl

## learn — Saving the postmortem to DataHub memory
- result: Postmortem "Postmortem: Null customer_id Ingestion from Postgres Source into Snowflake Orders Table" saved to DataHub. The next investigation of a similar incident will start from it.

Status: done · DataHub tool calls: 29

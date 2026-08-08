# Investigation 013abb17

## intake — Understanding the incident report
- info: Parsing incident report
- result: Symptom: nulls. Assets mentioned: orders, order_entry_db, order reports

## resolve — Resolving asset names to DataHub URNs
- tool_call: search(query=orders order_entry_db)
- tool_call: search(query=orders table)
- tool_call: search(query=orders database:order_entry_db)
- tool_call: search(query=orders container:urn:li:container:64a5f47928e5c808819f1385be)
- tool_call: search(query=orders platform:snowflake)
- tool_call: search(query=orders type:dataset)
- tool_call: get_entities(urns=['urn:li:dataset:(urn:li:dataPlatform:dbt,b2fd91.order_entry)
- warning: Ambiguity: Several versions of the 'orders' table exist (dbt, postgres, and snowflake). I have selected the snowflake version as it is the primary production table utilized in the Data Product 'Order Entry Analytics', has the highest interaction, and its metadata includes a note about the exact schema change (dropping NOT NULL) that caused the incident.
- result: Resolved to urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)

## recall — Searching incident memory in DataHub
- tool_call: search_documents(semantic_query=Why are there null values in the customer_id column of the o, query=orders NULL customer_id)
- tool_call: search_documents(semantic_query=postmortem for null values in customer_id column in orders t, query=postmortem incident null customer_id)
- tool_call: grep_documents(pattern=customer_id.*null, urns=['urn:li:document:ecomm-orders'])
- tool_call: grep_documents(urns=['urn:li:document:ecomm-orders'], pattern=null)
- result: No similar prior incidents in memory. Investigating from scratch.

## impact — Walking downstream lineage to compute blast radius
- tool_call: get_lineage(max_hops=3, upstream=False, urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- result: 29 downstream consumers affected, total impact score 30.08. Owners to notify: urn:li:corpGroup:b2fd91.1e0398a3-113f-475e-b6fc-32ab72a634d2, urn:li:corpGroup:b2fd91.ORG_BACKEND_ENG, urn:li:corpGroup:b2fd91.ORG_DATA_PLATFORM, urn:li:corpuser:b2fd91.EMP006, urn:li:corpuser:b2fd91.alex@example.com, urn:li:corpuser:b2fd91.brock1@example.com, urn:li:corpuser:b2fd91.bryan@example.com, urn:li:corpuser:b2fd91.jonny1@example.com, urn:li:corpuser:b2fd91.jonny2@example.com, urn:li:corpuser:b2fd91.kirk@example.com, urn:li:corpuser:b2fd91.marty@example.com, urn:li:corpuser:b2fd91.michael@example.com, urn:li:corpuser:b2fd91.patrick1@example.com, urn:li:corpuser:b2fd91.sam@example.com

## root_cause — Investigating upstream lineage for the root cause
- tool_call: get_lineage(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, upstream=True)
- tool_call: get_entities(urns=['urn:li:dataJob:(urn:li:dataFlow:(spark,b2fd91.import_table)
- tool_call: get_lineage(urn=urn:li:dataJob:(urn:li:dataFlow:(spark,b2fd91.import_table_o, upstream=True)
- tool_call: list_schema_fields(urn=urn:li:dataset:(urn:li:dataPlatform:s3,b2fd91.demo-data-buck)
- tool_call: list_schema_fields(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- tool_call: get_dataset_queries(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- tool_call: get_dataset_queries(urn=urn:li:dataset:(urn:li:dataPlatform:s3,b2fd91.demo-data-buck)
- tool_call: get_lineage_paths_between(target_urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, source_urn=urn:li:dataset:(urn:li:dataPlatform:s3,b2fd91.demo-data-buck)
- result: 2 hypothesis(es). Top: The upstream S3 data or the ingestion job process has introduced NULLs that violate the original schema assumptions, likely due to source data drift or ingestion logic errors. (confidence 70%)

## propose — Drafting the action plan
- info: Building action plan (dry-run)
- result: Action plan ready: 3 mutation(s) + 1 postmortem document. Awaiting human approval.

## commit — Writing approved changes back to DataHub
- info: Applied add_tags via mcp: Tagging the primary broken asset as degraded.
- info: Applied update_description via mcp: Adding incident warning to the broken asset description.
- info: Applied add_tags via mcp: Tagging high-impact downstream consumers as impacted.
- result: 3/3 mutations applied to DataHub. Audit log: var/audit-log.jsonl

## learn — Saving the postmortem to DataHub memory
- result: Postmortem "2026-08-08 Unexpected NULLs in Order Entry customer_id Column" saved to DataHub. The next investigation of a similar incident will start from it.

Status: done · DataHub tool calls: 20

# Investigation 8c7bff59

## intake — Understanding the incident report
- info: Parsing incident report
- result: Symptom: nulls. Assets mentioned: orders, order_entry_db, order reports

## resolve — Resolving asset names to DataHub URNs
- tool_call: search(query=orders order_entry_db)
- tool_call: search(query=orders)
- tool_call: get_entities(urns=['urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order)
- warning: Ambiguity: The snowflake table contains a explicit incident notification regarding the 'customer_id' NULL issue described in the report, making it the definitive source for this incident. Other representations (dbt, postgres) are alternative views/sources of the same underlying data.
- result: Resolved to urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)

## recall — Searching incident memory in DataHub
- tool_call: search_documents(semantic_query=investigate NULL values in customer_id column of orders tabl, query=orders table customer_id nulls)
- tool_call: grep_documents(pattern=orders.*customer_id, urns=['urn:li:document:shared-bb0cf27d-a698-4a1a-820e-831e6f8632d)
- result: Found 1 similar prior incident(s). Memory suggests: check urn:li:dataJob:(urn:li:dataFlow:(spark,b2fd91.import_table_orders_to_snowflake,b2fd91.default),b2fd91.import_table_orders_to_snowflake) first (Previous investigations suggested logic errors in the ingestion pipeline (incorrect join types or record filtering) result in NULLs for customer_id. Check the import_table_orders_to_snowflake data job.)

## impact — Walking downstream lineage to compute blast radius
- tool_call: get_lineage(upstream=False, urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, max_hops=3)
- result: 16 downstream consumers affected, total impact score 17.0. Owners to notify: urn:li:corpuser:b2fd91.EMP006, urn:li:corpuser:b2fd91.alex@example.com, urn:li:corpuser:b2fd91.brock1@example.com, urn:li:corpuser:b2fd91.bryan@example.com, urn:li:corpuser:b2fd91.jonny1@example.com, urn:li:corpuser:b2fd91.kirk@example.com, urn:li:corpuser:b2fd91.marty@example.com, urn:li:corpuser:b2fd91.michael@example.com, urn:li:corpuser:b2fd91.patrick1@example.com, urn:li:corpuser:b2fd91.sam@example.com

## root_cause — Investigating upstream lineage for the root cause
- tool_call: get_lineage(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, upstream=True)
- tool_call: get_entities(urns=['urn:li:dataJob:(urn:li:dataFlow:(spark,b2fd91.import_table)
- tool_call: get_lineage(urn=urn:li:dataJob:(urn:li:dataFlow:(spark,b2fd91.import_table_o, upstream=True)
- tool_call: list_schema_fields(keywords=['customer_id'], urn=urn:li:dataset:(urn:li:dataPlatform:s3,b2fd91.demo-data-buck)
- tool_call: list_schema_fields(keywords=['customer_id'], urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- tool_call: get_dataset_queries(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, source=MANUAL)
- tool_call: get_dataset_queries(source=SYSTEM, urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- tool_call: get_lineage_paths_between(source_urn=urn:li:dataset:(urn:li:dataPlatform:s3,b2fd91.demo-data-buck, target_urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- result: 1 hypothesis(es). Top: The data ingestion pipeline (spark data job) contains a logic error that is introducing NULLs into the customer_id column during the transfer from S3 to Snowflake. (confidence 90%)

## propose — Drafting the action plan
- info: Building action plan (dry-run)
- result: Action plan ready: 3 mutation(s) + 1 postmortem document. Awaiting human approval.

## commit — Writing approved changes back to DataHub
- info: Applied add_tags via mcp: Tagging degraded snowflake orders dataset with hindsight-degraded.
- info: Applied update_description via mcp: Adding incident warning to the snowflake orders dataset description.
- info: Applied add_tags via mcp: Tagging high-impact downstream assets (Power BI report and dbt order_details) as impacted.
- result: 3/3 mutations applied to DataHub. Audit log: var/audit-log.jsonl

## learn — Saving the postmortem to DataHub memory
- result: Postmortem "Investigation: NULL values in customer_id for order_entry_db.orders" saved to DataHub. The next investigation of a similar incident will start from it.

Status: done · DataHub tool calls: 14

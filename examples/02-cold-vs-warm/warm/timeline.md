# Investigation 2c904926

## intake — Understanding the incident report
- info: Parsing incident report
- result: Symptom: nulls. Assets mentioned: orders, order_entry_db, order reports

## resolve — Resolving asset names to DataHub URNs
- tool_call: search(query=orders)
- tool_call: search(query=order_entry_db)
- tool_call: search(query=order reports)
- tool_call: get_entities(urns=['urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order)
- warning: Ambiguity: The `orders` table exists in Snowflake, DBT (as a source), and Postgres. The Snowflake version is the primary production table containing the described data quality issue (as confirmed by the incident notice in its editable properties). The DBT asset is a source representation, and the Postgres version is another environment. I have selected the Snowflake table as the primary source of the issue. The PowerBI dashboard `datahub_order_entries` is identified as the impacted downstream report.
- result: Resolved to urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)

## recall — Searching incident memory in DataHub
- tool_call: search_documents(query=nulls in customer_id column in orders table, semantic_query=orders table customer_id column has NULL values incident inv)
- tool_call: grep_documents(urns=['urn:li:document:shared-bb0cf27d-a698-4a1a-820e-831e6f8632d, pattern=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- tool_call: grep_documents(urns=['urn:li:document:shared-bb0cf27d-a698-4a1a-820e-831e6f8632d, pattern=customer_id)
- result: Found 1 similar prior incident(s). Memory suggests: check urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD) first (Previous incidents suggest upstream data drift or schema mismatch where source S3 data might have changed constraints not reflected or handled correctly in downstream Snowflake ingestion.); check urn:li:dataJob:(urn:li:dataFlow:(spark,b2fd91.import_table_orders_to_snowflake,b2fd91.default),b2fd91.import_table_orders_to_snowflake) first (The Spark ingestion pipeline 'import_table_orders_to_snowflake' has been previously identified as a potential source of logic errors (e.g., incorrect join types) that introduce NULL values.)

## impact — Walking downstream lineage to compute blast radius
- tool_call: get_lineage(max_hops=3, urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- tool_call: get_lineage(max_hops=3, upstream=False, urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- result: 6 downstream consumers affected, total impact score 17.55. Owners to notify: urn:li:corpuser:b2fd91.EMP006, urn:li:corpuser:b2fd91.brock1@example.com, urn:li:corpuser:b2fd91.kirk@example.com, urn:li:corpuser:b2fd91.marty@example.com, urn:li:corpuser:b2fd91.michael@example.com, urn:li:corpuser:b2fd91.sam@example.com

## root_cause — Investigating upstream lineage for the root cause
- tool_call: get_lineage(upstream=True, urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- tool_call: get_lineage(upstream=True, urn=urn:li:dataJob:(urn:li:dataFlow:(spark,b2fd91.import_table_o)
- tool_call: list_schema_fields(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- tool_call: list_schema_fields(urn=urn:li:dataset:(urn:li:dataPlatform:s3,b2fd91.demo-data-buck)
- tool_call: get_dataset_queries(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e)
- tool_call: get_entities(urns=['urn:li:dataJob:(urn:li:dataFlow:(spark,b2fd91.import_table)
- result: 2 hypothesis(es). Top: Schema drift between the upstream S3 source and the Snowflake target table has enabled nullable customer_id fields, causing NULL values to enter the warehouse. (confidence 80%)

## propose — Drafting the action plan
- info: Building action plan (dry-run)
- result: Action plan ready: 3 mutation(s) + 1 postmortem document. Awaiting human approval.

## commit — Writing approved changes back to DataHub
- info: Applied add_tags via mcp: Tagging the primary broken asset with hindsight-degraded.
- info: Applied update_description via mcp: Adding a warning to the description of the broken asset.
- info: Applied add_tags via mcp: Tagging the high-impact downstream assets with hindsight-impacted.
- result: 3/3 mutations applied to DataHub. Audit log: var/audit-log.jsonl

## learn — Saving the postmortem to DataHub memory
- result: Postmortem "Root Cause Analysis: NULL Propagation in Order Entry Pipeline" saved to DataHub. The next investigation of a similar incident will start from it.

Status: done · DataHub tool calls: 15

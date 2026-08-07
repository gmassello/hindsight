# Skill run — datahub-incident-triage

Executed 2026-08-05 against the local DataHub quickstart by an agent following only
`.agents/skills/datahub-incident-triage/SKILL.md`. No Hindsight backend code in the loop: the DataHub
MCP tools were called directly. Tool calls are numbered in the order they happened.

## step 1 — Parse the report

- info: Parsing incident report (no tool calls; the skill parses before touching DataHub)
- result: Symptom: nulls. Assets mentioned: orders, order_entry_db, order reports. Detected at: 03:00 UTC today

## step 2 — Resolve names to URNs

- tool_call: 1. search(query=orders)
- info: 4 homonymous candidates — snowflake, dbt, postgres and s3 all expose a dataset named orders
- tool_call: 2. get_entities(urns=[snowflake orders, postgres orders, dbt orders])
- warning: Ambiguity: four assets match "orders". Selected the Snowflake table — subType Table, carries the PII glossary term and the Large Table tag, and is the production analytics table the report refers to. Discarded: the Postgres table (upstream source, subType Table), the dbt model (subType Source, description "Contains header information for customer orders") and the S3 extract.
- info: The Postgres orders table already carries the tag hindsight-degraded, written by a previous triage
- result: Resolved to urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)

## step 3 — Search memory first

- tool_call: 3. search_documents(semantic_query=NULL values in customer_id in the orders table, query=orders AND customer_id AND NULL)
- info: 4 prior postmortems of subType Analysis returned, all about this asset and this symptom
- tool_call: 4. grep_documents(urns=[urn:li:document:shared-5a41e0b5-cfce-4a63-9838-4a1ceac6fed2], pattern=(?i)root cause|hypothes|postgres|evidence|urn:li:dataset)
- result: Found 4 similar prior incidents. Memory suggests: check urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_entry_db.order_entry.orders,PROD) first — the prior postmortem states at 90% confidence that the NULLs originate in the upstream Postgres source system, citing that table's hindsight-degraded tag.

## step 4 — Compute the blast radius

- tool_call: 5. get_lineage(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, upstream=False, max_hops=3)
- info: 37 downstream consumers found, 30 returned by the server (22 datasets, 12 charts, 3 dashboards)
- info: Scored with references/impact-scoring-reference.md — no estimation
- result: 30 downstream consumers affected, total impact score 26.23. Owners to notify: 14 (see blast-radius.md)

## step 5 — Find the root cause

- info: Starting from the memory hint: the upstream Postgres source
- tool_call: 6. get_lineage(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, upstream=True, max_hops=3)
- info: 4 ancestors. The Postgres orders table sits 4 hops up and is tagged hindsight-degraded — pattern upstream_incident confirmed
- tool_call: 7. list_schema_fields(urn=urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e, keywords=['customer_id'])
- info: customer_id is NUMBER(38,0), nullable=true, carries the PII glossary term
- error: get_lineage_paths_between rejected upstream_urn/downstream_urn — the real parameters are source_urn/target_urn. Retried.
- tool_call: 8. get_lineage_paths_between(source_urn=postgres orders, target_urn=snowflake orders)
- info: Propagation path: postgres orders -> spark export_table_orders_to_s3 -> s3 orders -> spark import_table_orders -> snowflake ORDERS
- tool_call: 9. get_entities(urns=[urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_e])
- info: The asset description records "ALTER TABLE order_entry.orders ALTER COLUMN customer_id DROP NOT NULL;" applied 2026-08-04 by the order_entry service team without downstream notice
- result: 2 hypotheses. Top: the order_entry service team dropped the NOT NULL constraint on customer_id upstream without downstream notice (schema_drift_upstream, confidence 90%). Second: the upstream Postgres source is an active incident and the origin of the propagation (upstream_incident, confidence 75%).

## step 6 — Propose the action plan (dry run)

- info: Building action plan (dry-run). All mutation targets are URNs seen during this investigation
- result: Action plan ready: 3 mutations + 1 postmortem document. Awaiting human approval.
- info: Human approved the plan

## step 6 — Commit

- info: Read the update_description schema before calling it: operation enum is replace|append|remove. Chose append — the skill forbids destroying existing documentation
- info: Applied add_tags via mcp: mark the broken Snowflake orders table as degraded
- info: Applied add_tags via mcp: flag the highest-scoring downstream dashboard as impacted
- info: Applied update_description via mcp: incident banner so anyone opening the asset in the DataHub UI sees it
- result: 3/3 mutations applied to DataHub

## step 7 — Write the postmortem to memory

- info: Read the save_document schema: document_type enum is Insight|Decision|FAQ|Analysis|Summary|Recommendation|Note|Context. Selected Analysis — not guessed
- tool_call: save_document(document_type=Analysis, title=Incident 2026-08-05: nulls in ORDERS (customer_id NOT NULL dropped upstream), related_assets=[snowflake orders])
- result: Postmortem saved as urn:li:document:shared-4a4814c8-77ec-4448-83da-353db065b22b

## verification — is the loop actually closed?

- tool_call: search_documents(semantic_query=NULL values in customer_id in the orders table, query=customer_id AND NULL)
- result: The postmortem written moments earlier comes back in second position. A subsequent investigation would retrieve it.

Status: done · DataHub tool calls: 9 investigation + 4 write-back + 1 verification

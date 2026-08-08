# Scenario 02 — Cold vs. warm ★

The same incident, investigated twice against the same catalog. The only difference: the warm run's `recall` phase found the postmortem the cold run had written to DataHub minutes earlier.

Input (identical in both runs):

> orders in order_entry_db is showing NULL values in customer_id since 03:00 UTC today, downstream order reports look wrong

| Run | Memory | DataHub tool calls | Consumers swept | Outcome |
|---|---|---|---|---|
| [cold](cold/) | empty | **20** | 29 | Investigated from scratch: explored downstream lineage, upstream lineage, schemas and query history before converging on the S3 source and the Spark ingestion job |
| [warm](warm/) | 1 postmortem (written by the cold run) | **15** | 6 | `recall` retrieved the prior postmortem and steered `root_cause` straight at the ingestion path |

25% fewer DataHub calls, same conclusion.

The steering moment, verbatim from [`warm/timeline.md`](warm/timeline.md):

> Found 1 similar prior incident(s). Memory suggests: check urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD) first (Previous incidents suggest upstream data drift or schema mismatch where source S3 data might have changed constraints not reflected or handled correctly in downstream Snowflake ingestion.); check urn:li:dataJob:(urn:li:dataFlow:(spark,b2fd91.import_table_orders_to_snowflake,b2fd91.default),b2fd91.import_table_orders_to_snowflake) first (The Spark ingestion pipeline 'import_table_orders_to_snowflake' has been previously identified as a potential source of logic errors (e.g., incorrect join types) that introduce NULL values.)

The honest reading of the fourth column: memory bought speed and cost coverage. Pointed at the suspect from the first turn, the warm run spent fewer calls walking downstream and reported 6 consumers against the cold run's 29. Both landed on the same root cause; only the cold run produced the full blast radius.

The memory lives inside DataHub (a document saved with `save_document`, retrieved with `search_documents`/`grep_documents`) — no side database. Every investigation makes the next one cheaper.

Both runs ship their raw event stream. `hindsight replay examples/02-cold-vs-warm/cold` reprints the whole investigation with Docker off and no API key.

# Scenario 02 — Cold vs. warm ★

The same incident, investigated twice against the same catalog. The only difference: the warm run's `recall` phase found the postmortem the cold run had written to DataHub minutes earlier.

Input (identical in both runs):

> orders in order_entry_db is showing NULL values in customer_id since 03:00 UTC today, downstream order reports look wrong

| Run | Memory | DataHub tool calls | Outcome |
|---|---|---|---|
| [cold](cold/) | empty | **29** | Investigated from scratch: explored downstream lineage, upstream lineage, schemas and query history before converging on the Postgres source |
| [warm](warm/) | 1 postmortem (written by the cold run) | **17** | `recall` retrieved the prior postmortem and steered `root_cause` straight to the upstream Postgres orders table |

41% fewer DataHub calls, same conclusion.

The steering moment, verbatim from [`warm/timeline.md`](warm/timeline.md):

> Found 1 similar prior incident(s). Memory suggests: check urn:li:dataset:(urn:li:dataPlatform:postgres,b2fd91.order_entry_db.order_entry.orders,PROD) first (Check upstream Postgres orders table for NULL values, as previous incidents indicated the nulls originated there.)

The memory lives inside DataHub (a document saved with `save_document`, retrieved with `search_documents`/`grep_documents`) — no side database. Every investigation makes the next one cheaper.

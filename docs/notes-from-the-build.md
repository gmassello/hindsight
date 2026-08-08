# Notes from the build

Things that cost hours against a real DataHub and a real model, written down so they cost you minutes.

**`datahub datapack load` returns before the lineage graph exists.** The ingestion reports success in under a second while the index fills in for minutes. A run started too early produces a real-looking investigation with a blast radius that is quietly wrong — no error, no empty result, just fewer consumers than the graph actually has. Wait for the quickstart to report healthy *and* spot-check a lineage query in the UI before the first run.

**Two runs against the same asset silently overwrite each other's incident banner.** `update_description` replaces; it does not append. `verify` found this, not the author: [`examples/02-cold-vs-warm/cold/verify.txt`](../examples/02-cold-vs-warm/cold/verify.txt) reports `verified 5/6` and the one failure is the banner. Every run had reported success. This is the entire argument for verifying through a second channel — the failing file ships as it came out.

**Gemini rejects `$ref`/`$defs` and unknown keys in function declarations.** All the normalization — ref inlining, key dropping, type uppercasing — lives in one place, `llm/gemini_provider.py::_clean_schema`, because splitting it across layers produces schemas that are valid at each step and invalid at the end. The trap inside the trap: a property legitimately *named* `title` under `properties` has to survive the same pass that drops `title` as schema metadata.

**`MAX_TOKENS` is 16384 for a reason.** A `submit_*` payload carrying 30 consumers with full URNs blows past anything smaller, and the failure mode is the model going silent halfway through a JSON object rather than raising an explicit error.

**`save_document` needs a `document_type` from a server-defined enum** (`Analysis`, `Note`, …). Read it from the live schema; a guessed value is a rejected write — `learn` reads the enum at runtime.

**The MCP server hides the document tools entirely when the catalog has zero documents.** `recall` has to treat their absence as a cold start rather than an error, or the very first run against a fresh install fails on the phase whose job is to find nothing.

**`grep_documents` takes a `urns` argument** — it narrows an existing result set, it does not search the catalog. And `get_lineage_paths_between` takes `source_urn`/`target_urn`, not `upstream_urn`/`downstream_urn`. Both were guessed once and both cost a wasted turn — see [`examples/04-skill-portability`](../examples/04-skill-portability).

**An agent that summarises its own postmortem quietly breaks the memory loop.** `grep_documents` matches literal text, so a prose summary of a blast radius is a document the next investigation cannot use. The postmortem has to carry every row, every owner URN and the largest hop count actually observed. Found by running the Skill end to end — see [`examples/04-skill-portability`](../examples/04-skill-portability).

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Hindsight is a hackathon project (DataHub Agent Hackathon, track "Agents That Do Real Work"): an on-call agent that diagnoses data incidents by walking DataHub lineage, proposes ranked root causes, and writes results (tags, descriptions, owners, postmortem documents) back into DataHub with a human approval gate. The full design and schedule live in `docs/plan-track-autonomous-agents.md`.

## Commands

All from `backend/` (Python 3.13, managed with uv):

```bash
uv sync                                  # create .venv and install deps
.venv/bin/ruff check src tests           # lint (gate before finishing any task)
.venv/bin/pytest                         # run all tests
.venv/bin/pytest tests/test_lineage.py -k test_impact_score_formula   # single test
.venv/bin/hindsight investigate "<incident text>" [--auto-approve]    # full agent run (CLI)
.venv/bin/hindsight serve                # FastAPI on :8000
```

Local DataHub (required for end-to-end runs; Docker runs via colima on this machine):

```bash
colima start --cpu 4 --memory 8
datahub docker quickstart                # UI: http://localhost:9002 (datahub/datahub)
datahub datapack load showcase-ecommerce
```

`backend/.env` needs `GEMINI_API_KEY` (default provider). `DATAHUB_GMS_TOKEN` stays empty for quickstart (metadata-service auth is disabled there).

## Architecture

The core design decision: **a deterministic phase state machine with an LLM inside each phase**, not a free ReAct loop. `agent/orchestrator.py` defines two phase lists split by the human gate — `investigate()` runs intake → resolve → recall → impact → root_cause → propose, then stops with status `awaiting_approval`; `commit_and_learn()` runs commit → learn after approval. Each phase entry carries a `critical` flag: critical phases abort the run on failure, non-critical ones emit an error event and continue with partial state.

Data flows through one shared Pydantic object, `InvestigationState` (`models.py`), that phases mutate via `Ctx` (`agent/context.py`). Phases are async generators yielding `TimelineEvent`s — the same event stream feeds the CLI renderer (`cli.py`) and the SSE endpoint (`api/investigations.py`).

Four phases (resolve, recall, impact, root_cause) are mini tool-using agents built on `agent/phase_agent.py`: a generic loop that gives the LLM a **whitelisted subset of DataHub MCP tools** plus a terminal `submit_*` tool whose schema is a Pydantic model. Key behaviors in that loop: premature submits (in the same turn as other tools) are rejected, a "last chance" message fires two turns before the `PHASE_MAX_TURNS` budget runs out, and tool failures become error results instead of crashes. intake and propose have no tools and use `llm/structured.py::complete_structured` instead. impact deliberately keeps math out of the LLM: the model reports raw consumers, `datahub/lineage.py` computes scores deterministically.

DataHub access (`datahub/mcp_client.py`) has two transports: streamable HTTP when `DATAHUB_MCP_URL` is set (DataHub Cloud), otherwise it spawns `uvx mcp-server-datahub` over stdio with `TOOLS_IS_MUTATION_ENABLED=true`. Tool schemas are discovered at runtime — never hardcode arg shapes; `propose` injects the live mutation schemas into its prompt, and `learn` reads the `document_type` enum from the live `save_document` schema. Read/write tool split uses MCP `readOnlyHint` annotations with a name-prefix fallback. Mutations that fail over MCP retry through `datahub/graphql_fallback.py` (GMS GraphQL, also creates tags via `ensure_tag`).

The memory loop is the differentiator: `learn` saves the postmortem as a DataHub document; the next run's `recall` phase retrieves it via `search_documents`/`grep_documents` and turns it into `investigation_hints` that steer `root_cause`. Note the MCP server **hides the document tools when the catalog has zero documents** — recall treats their absence as cold start, not an error.

## Gotchas learned the hard way

- Gemini rejects `$ref`/`$defs` and unknown schema keys in function declarations; all normalization (ref inlining, key dropping, type uppercasing) lives in `llm/gemini_provider.py::_clean_schema` and must not be split across layers. Beware `_DROP_KEYS` vs. actual properties named `title` — property names under `properties` are never dropped.
- Large `submit_*` payloads (30 consumers with URNs) exceed small `MAX_TOKENS`; it is 16384 for a reason.
- `save_document` requires `document_type` from a server-defined enum (`Analysis`, `Note`, ...) — read it from the schema, don't guess.
- Tests mock both the LLM (`fake_llm` fixture) and DataHub (`FakeDataHub` in `tests/conftest.py`); orchestrator tests monkeypatch the phase lists with 4-tuples `(name, description, run, critical)`.

## Conventions

- Code, docs, prompts and user-facing strings in English; conversation with the user in Spanish.
- The repo owner's global rules apply: no code comments, no JavaDocs-style docs, surgical diffs.
- Scope discipline: out of scope by design are warehouse SQL execution, PagerDuty/Slack/Jira integrations, multi-user auth, and incident detection/monitoring (see plan §3).

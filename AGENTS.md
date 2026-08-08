# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Hindsight is a hackathon project (DataHub Agent Hackathon, track "Agents That Do Real Work"): an on-call agent that diagnoses data incidents by walking DataHub lineage, proposes ranked root causes, and writes results (tags, descriptions, owners, postmortem documents) back into DataHub with a human approval gate. `docs/design.md` is the frozen design document written before implementation — useful for the *why*, but it describes what was planned, not what was built; this file and `README.md` describe the system as it is. Delivery status lives in `SUBMISSION.md`.

## Commands

All from `backend/` (Python 3.13, managed with uv):

```bash
uv sync                                  # create .venv and install deps
.venv/bin/ruff check src tests           # lint (gate before finishing any task)
.venv/bin/pytest                         # run all tests
.venv/bin/pytest tests/test_lineage.py -k test_impact_score_formula   # single test
.venv/bin/hindsight investigate "<incident text>" [--auto-approve]    # full agent run (CLI)
.venv/bin/hindsight replay ../examples/02-cold-vs-warm/cold           # reprint a captured run offline
.venv/bin/hindsight verify ../examples/01-schema-drift                # re-read the mutations from DataHub
.venv/bin/python ../scenarios/build_recordings.py                     # re-sync frontend/public/recordings.json from examples/
.venv/bin/hindsight serve                # FastAPI on :8000
```

Local DataHub (required for end-to-end runs; Docker runs via colima on this machine):

```bash
colima start --cpu 4 --memory 8
datahub docker quickstart                # UI: http://localhost:9002 (datahub/datahub)
datahub datapack load showcase-ecommerce
```

`backend/.env` needs `GEMINI_API_KEY` (default provider). `DATAHUB_GMS_TOKEN` stays empty for quickstart (metadata-service auth is disabled there).

Frontend (from `frontend/`, React + Vite + TS):

```bash
npm install
npm run dev                              # Vite dev server on :5173 (CORS default already allows it)
VITE_DEMO_MODE=1 npm run dev             # replay mode: plays back examples/, no backend needed
npm run build                            # tsc + vite build — the frontend gate before finishing any task
npm run lint                             # oxlint
```

## Architecture

The core design decision: **a deterministic phase state machine with an LLM inside each phase**, not a free ReAct loop. `agent/orchestrator.py` defines two phase lists split by the human gate — `investigate()` runs intake → resolve → recall → impact → root_cause → propose, then stops with status `awaiting_approval`; `commit_and_learn()` runs commit → learn after approval. Each phase entry carries a `critical` flag: critical phases abort the run on failure, non-critical ones emit an error event and continue with partial state.

Data flows through one shared Pydantic object, `InvestigationState` (`models.py`), that phases mutate via `Ctx` (`agent/context.py`). Phases are async generators yielding `TimelineEvent`s — the same event stream feeds the CLI renderer (`cli.py`) and the SSE endpoint (`api/investigations.py`).

Four phases (resolve, recall, impact, root_cause) are mini tool-using agents built on `agent/phase_agent.py`: a generic loop that gives the LLM a **whitelisted subset of DataHub MCP tools** plus a terminal `submit_*` tool whose schema is a Pydantic model. Key behaviors in that loop: premature submits (in the same turn as other tools) are rejected, a "last chance" message fires two turns before the `PHASE_MAX_TURNS` budget runs out, and tool failures become error results instead of crashes. intake and propose have no tools and use `llm/structured.py::complete_structured` instead. impact deliberately keeps math out of the LLM: the model reports raw consumers, `datahub/lineage.py` computes scores deterministically.

DataHub access (`datahub/mcp_client.py`) has two transports: streamable HTTP when `DATAHUB_MCP_URL` is set (DataHub Cloud), otherwise it spawns `uvx mcp-server-datahub` over stdio with `TOOLS_IS_MUTATION_ENABLED=true`. Tool schemas are discovered at runtime — never hardcode arg shapes; `propose` injects the live mutation schemas into its prompt, and `learn` reads the `document_type` enum from the live `save_document` schema. Read/write tool split uses MCP `readOnlyHint` annotations with a name-prefix fallback. Mutations that fail over MCP retry through `datahub/graphql_fallback.py` (GMS GraphQL, also creates tags via `ensure_tag`).

The memory loop is the differentiator: `learn` saves the postmortem as a DataHub document; the next run's `recall` phase retrieves it via `search_documents`/`grep_documents` and turns it into `investigation_hints` that steer `root_cause`.

The frontend (`frontend/src/`) is a single-page React app with zero runtime deps beyond react/react-dom: one custom hook `useInvestigation.ts` owns all state and the SSE lifecycle, `App.tsx` renders panels progressively as each phase's `result` event arrives. SSE contract quirks it depends on: the SSE event *name* is the TimelineEvent `kind` (not the phase), so every kind plus `state`/`agent_error` needs its own `addEventListener`; the stream is one-shot (409 on reopen), so the EventSource must be closed on the terminal `state`/`agent_error` frames to prevent the browser's auto-reconnect, and it is opened inside the `start()` handler (not an effect) so StrictMode's double mount can't hit the 409; `/approve` is a blocking 30–60s call, rendered as a "committing" state whose returned events are appended to the timeline afterwards.

## Gotchas learned the hard way

The runtime ones live in [`docs/notes-from-the-build.md`](docs/notes-from-the-build.md) — Gemini schema cleaning (and the `_DROP_KEYS` vs. a property actually named `title` trap), `MAX_TOKENS`, the `document_type` enum, the document tools the MCP server hides on an empty catalog, and the real signatures of `grep_documents` / `get_lineage_paths_between`, plus the `datapack load` indexing race and the incident-banner overwrite `verify` caught. Read them before touching `llm/` or a phase's tool list.

Only in here:

- Tests mock both the LLM (`fake_llm` fixture) and DataHub (`FakeDataHub` in `tests/conftest.py`); orchestrator tests monkeypatch the phase lists with 4-tuples `(name, description, run, critical)`.

## Conventions

- Code, docs, prompts and user-facing strings in English; conversation with the user in Spanish.
- The repo owner's global rules apply: no code comments, no JavaDocs-style docs, surgical diffs.
- Scope discipline: the out-of-scope table in [`docs/design.md`](docs/design.md) §3 *Scope: what is in and what is out* lists the six things ruled out by design.
- Frontend: no new runtime dependencies (native `EventSource`/`fetch`, plain CSS, no router/state/chart libraries); no frontend test framework — `npm run build` is the gate.

# Hindsight

**The on-call agent for your data platform.** When something breaks, Hindsight walks the DataHub lineage graph to compute who is affected, proposes a root cause backed by incidents you already solved, and writes the postmortem back into DataHub — so the next diagnosis starts where this one ended.

Built for the [Build with DataHub: The Agent Hackathon](https://datahub.devpost.com/) — track *Agents That Do Real Work*: agents that **read** DataHub to understand what is connected to what, **take action**, and **write the results back**.

## The closed loop

Hindsight is not a chatbot over metadata. Every investigation makes the next one smarter, and that knowledge lives **inside DataHub**, not in a side database:

1. **Read** — multi-hop lineage traversal, schema inspection, query history, and the postmortems previous runs stored as DataHub documents.
2. **Act** — blast-radius scoring, ranked root-cause hypotheses with cited evidence, an action plan with a rationale per mutation.
3. **Write back** — tags (`hindsight-degraded`, `hindsight-impacted`), incident banners in asset descriptions, owner assignments for governance gaps, and a structured postmortem document that the next run's memory search retrieves.

A later run even benefits from the write-back directly: an ancestor already tagged `hindsight-degraded` is evidence for the *upstream incident* hypothesis — the system reads its own past actions.

## Architecture

```
 incident text ──► intake ──► resolve ──► recall ★ ──► impact ──► root_cause ──► propose
                  (LLM)      (agent)     (agent)      (agent)     (agent)       (LLM)
                                                                                  │
                                                                          [ human gate ]
                                                                                  │
                                          learn ★ ◄─────────────── commit ◄───────┘
                                         (code)                    (code)
```

- **Deterministic phase pipeline, not a free ReAct loop.** The orchestrator decides *which* phase runs and *which* DataHub tools are available in it; the LLM decides *how* to interpret the results. Each phase emits timeline events (SSE-ready), can be tested in isolation, and degrades gracefully: non-critical phases fail into "continue with partial information" instead of killing the run.
- **Per-phase toolsets.** Investigation phases (1–4) only ever see read tools; mutation tools exist only in `commit`/`learn`. The model cannot write while it should be reading.
- **Memory before investigation.** `recall` runs *before* `impact`/`root_cause`, and what it retrieves becomes `investigation_hints` that direct where the root-cause search looks first. Memory steers the investigation instead of decorating it.
- **All math and writes are code.** The LLM reports facts (consumers found, hops, owners); the impact score is a deterministic formula, the mutations are executed by code with an audit log. `impact(consumer) = type_weight × 1/(1+hops) × owner/criticality/domain multipliers`.
- **Human gate by default.** The agent can run autonomously (`--auto-approve`), but the default is a dry-run plan awaiting explicit approval. Every applied mutation is recorded in a JSONL audit log with timestamp, tool, URN, args and rationale.
- **MCP first, GraphQL fallback.** DataHub access goes through the official [`mcp-server-datahub`](https://github.com/acryldata/mcp-server-datahub) (stdio, mutations enabled). If a mutation tool is missing or fails, the same mutation is applied through the GMS GraphQL API.

## Quickstart

Prerequisites: Docker (or colima), Python 3.13, [uv](https://docs.astral.sh/uv/), a Gemini / Anthropic / Bedrock key.

```bash
# 1. Local DataHub with sample lineage
uv tool install acryl-datahub
datahub docker quickstart                       # UI at http://localhost:9002 (datahub/datahub)
datahub datapack load showcase-ecommerce

# 2. Backend
cd backend
uv sync
cp ../.env.example .env                         # set GEMINI_API_KEY (or provider of choice)

# 3. Investigate an incident
.venv/bin/hindsight investigate \
  "orders table in order_entry_db is showing nulls in customer_id since 03:00 UTC today"
```

The CLI streams the investigation timeline, renders the proposed mutations as a dry-run diff, asks for approval, applies the changes, and saves the postmortem. Open the asset in the DataHub UI to see the tags, the incident banner and the document.

Run it twice: the second run's `recall` phase finds the postmortem the first run wrote and starts from its conclusions.

### API server

```bash
.venv/bin/hindsight serve                       # FastAPI on :8000
```

- `POST /investigations` `{"text": "..."}` → create
- `GET /investigations/{id}/stream` → SSE timeline (runs phases up to the human gate)
- `POST /investigations/{id}/approve` → commit + learn
- `POST /investigations/{id}/reject`

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DATAHUB_GMS_URL` | `http://localhost:8080` | GMS endpoint |
| `DATAHUB_GMS_TOKEN` | empty | PAT; empty works with quickstart (auth disabled) |
| `DATAHUB_MCP_URL` | empty | Streamable-HTTP MCP endpoint (DataHub Cloud); empty spawns local stdio server |
| `DATAHUB_MCP_COMMAND` | `uvx mcp-server-datahub` | Command for the stdio MCP server |
| `LLM_PROVIDER` | `gemini` | `gemini` \| `anthropic` \| `bedrock` |
| `HINDSIGHT_AUTO_APPROVE` | `false` | Skip the human gate (deliberately off by default) |
| `HINDSIGHT_MAX_HOPS` | `3` | Downstream lineage depth |
| `PHASE_MAX_TURNS` | `12` | LLM turn budget per phase |
| `AUDIT_LOG_PATH` | `var/audit-log.jsonl` | Mutation audit log |

## Project layout

```
backend/src/hindsight/
├── agent/
│   ├── orchestrator.py     # phase state machine, graceful degradation
│   ├── phase_agent.py      # generic LLM-with-tools loop (premature-submit guard, turn budget)
│   └── phases/             # intake, resolve, recall ★, impact, root_cause, propose, commit, learn ★
├── datahub/
│   ├── mcp_client.py       # MCP session (stdio or HTTP), read/write tool split via annotations
│   ├── graphql_fallback.py # mutations via GMS GraphQL when MCP can't
│   └── lineage.py          # deterministic blast-radius scoring
├── llm/                    # provider-agnostic layer: gemini / anthropic / bedrock + structured output
├── memory/postmortem.py    # postmortem markdown rendering
├── safety/                 # dry-run rendering + JSONL audit log
├── api/                    # FastAPI + SSE
└── cli.py                  # `hindsight investigate` / `hindsight serve`
```

## Tests

```bash
cd backend
.venv/bin/ruff check src tests
.venv/bin/pytest
```

Unit tests mock the LLM and the MCP client; the scoring formula, the phase loop guards, the postmortem rendering and the orchestrator's failure policy are covered.

## License

Apache 2.0

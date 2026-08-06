# Hindsight

**The on-call agent for your data platform.** When something breaks, Hindsight walks the DataHub lineage graph to compute who is affected, proposes a root cause backed by incidents you already solved, and writes the postmortem back into DataHub — so the next diagnosis starts where this one ended.

Built for the [Build with DataHub: The Agent Hackathon](https://datahub.devpost.com/) — track _Agents That Do Real Work_: agents that **read** DataHub to understand what is connected to what, **take action**, and **write the results back**.

## The closed loop

Hindsight is not a chatbot over metadata. Every investigation makes the next one smarter, and that knowledge lives **inside DataHub**, not in a side database:

1. **Read** — multi-hop lineage traversal, schema inspection, query history, and the postmortems previous runs stored as DataHub documents.
2. **Act** — blast-radius scoring, ranked root-cause hypotheses with cited evidence, an action plan with a rationale per mutation.
3. **Write back** — tags (`hindsight-degraded`, `hindsight-impacted`), incident banners in asset descriptions, owner assignments for governance gaps, and a structured postmortem document that the next run's memory search retrieves.

A later run even benefits from the write-back directly: an ancestor already tagged `hindsight-degraded` is evidence for the _upstream incident_ hypothesis — the system reads its own past actions.

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

### Design decisions

- **Deterministic phase pipeline, not a free ReAct loop.** The orchestrator decides _which_ phase runs and _which_ DataHub tools are available in it; the LLM decides _how_ to interpret the results. Each phase emits timeline events (SSE-ready), can be tested in isolation, and degrades gracefully: non-critical phases fail into "continue with partial information" instead of killing the run.
- **Per-phase toolsets.** Investigation phases (1–4) only ever see read tools; mutation tools exist only in `commit`/`learn`. The model cannot write while it should be reading.
- **Memory before investigation.** `recall` runs _before_ `impact`/`root_cause`, and what it retrieves becomes `investigation_hints` that direct where the root-cause search looks first. Memory steers the investigation instead of decorating it.
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

### Web UI

```bash
# terminal 1
cd backend && .venv/bin/hindsight serve         # FastAPI on :8000

# terminal 2
cd frontend && npm install && npm run dev       # Vite on http://localhost:5173
```

### One-command bring-up (Docker)

With DataHub quickstart already running (step 1 above):

```bash
GEMINI_API_KEY=<your-key> docker compose up --build
```

Backend on `http://localhost:8000`, frontend on `http://localhost:5173`. The backend container reaches the host's DataHub through `host.docker.internal:8080`, so no compose changes are needed on macOS or Linux.

Single-page React app: submit an incident and watch the evidence timeline stream live over SSE while the panels fill in as each phase completes — resolved asset, "we've seen this before" (memory), blast radius ranked by impact score, root-cause hypotheses with confidence bars, and the proposed action plan rendered as a diff with **Approve / Reject** buttons (the human gate). After approval, each mutation shows its commit result and the postmortem reference.

If the API runs elsewhere, set `VITE_API_URL` in `frontend/.env` (defaults to `http://localhost:8000`).

### API server

```bash
.venv/bin/hindsight serve                       # FastAPI on :8000
```

- `POST /investigations` `{"text": "..."}` → create
- `GET /investigations/{id}/stream` → SSE timeline (runs phases up to the human gate)
- `POST /investigations/{id}/approve` → commit + learn
- `POST /investigations/{id}/reject`

## Configuration

| Variable                 | Default                  | Purpose                                                                       |
| ------------------------ | ------------------------ | ----------------------------------------------------------------------------- |
| `DATAHUB_GMS_URL`        | `http://localhost:8080`  | GMS endpoint                                                                  |
| `DATAHUB_GMS_TOKEN`      | empty                    | PAT; empty works with quickstart (auth disabled)                              |
| `DATAHUB_MCP_URL`        | empty                    | Streamable-HTTP MCP endpoint (DataHub Cloud); empty spawns local stdio server |
| `DATAHUB_MCP_COMMAND`    | `uvx mcp-server-datahub` | Command for the stdio MCP server                                              |
| `LLM_PROVIDER`           | `gemini`                 | `gemini` \| `anthropic` \| `bedrock`                                          |
| `HINDSIGHT_AUTO_APPROVE` | `false`                  | Skip the human gate (deliberately off by default)                             |
| `HINDSIGHT_MAX_HOPS`     | `3`                      | Downstream lineage depth                                                      |
| `PHASE_MAX_TURNS`        | `12`                     | LLM turn budget per phase                                                     |
| `AUDIT_LOG_PATH`         | `var/audit-log.jsonl`    | Mutation audit log                                                            |

## Demo scenarios

`scenarios/scenarios.yaml` defines three reproducible scenarios; `examples/` holds the real artifacts (input, timeline, blast radius, postmortem, audit log). The first three were captured with `hindsight investigate ... --report <dir>`; the fourth is a run of the Skill alone, captured by hand:

1. [`01-schema-drift`](examples/01-schema-drift/) — a simulated upstream migration (`scenarios/break_schema.py`) drops the `customer_id` NOT NULL constraint; the agent finds the migration note on the source, tags the degraded and impacted assets, and saves the postmortem.
2. [`02-cold-vs-warm`](examples/02-cold-vs-warm/) ★ — the same incident twice. The cold run investigates from scratch (**29 DataHub tool calls**); the warm run's `recall` phase retrieves the postmortem the cold run just wrote and goes straight to the suspect ancestor (**17 calls, 41% fewer**). The two timelines sit side by side.
3. [`03-orphaned-asset`](examples/03-orphaned-asset/) — a stale table nobody owns: besides the incident actions, the agent proposes `add_owners` to close the governance gap.
4. [`04-skill-portability`](examples/04-skill-portability/) — the same incident as scenario 1, investigated by an agent driven only by the open source Skill, with no Hindsight code in the loop. Same asset, same owners, converging root cause.

`scenarios/seed_incidents.py` loads six resolved historical postmortems into DataHub documents so `recall` has memory to work with.

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

frontend/src/
├── useInvestigation.ts     # all state + SSE lifecycle in one hook
├── App.tsx                 # layout: live timeline | progressive result panels
└── components/             # Timeline, RecallPanel, BlastRadius, HypothesesPanel, PlanPanel

scenarios/                  # seed_incidents.py, break_schema.py, scenarios.yaml
examples/                   # real captured runs for the three demo scenarios
skills/                     # datahub-incident-triage: this workflow as a portable Agent Skill
.claude/skills →            # symlink to skills/, so Claude Code discovers them in this repo
docker-compose.yml          # backend + frontend against an external DataHub quickstart
```

The frontend is deliberately dependency-free beyond React: native `EventSource` for streaming, plain CSS for the theme, no router or state library.

## The workflow as a portable Skill

[`skills/datahub-incident-triage/`](skills/datahub-incident-triage/) distills this agent into an [Agent Skills](https://skills.sh) package: the same seven-step procedure — memory first, blast radius, ranked hypotheses, approval gate, postmortem — as plain instructions, with no Python involved. Any compatible CLI (Claude Code, Cursor, Codex, Copilot, Gemini CLI, Windsurf) with DataHub connected gets the behaviour without cloning this repo.

It is written against the same DataHub MCP tool names Hindsight uses, with `datahub` CLI fallbacks, and follows the conventions of [`datahub-project/datahub-skills`](https://github.com/datahub-project/datahub-skills). [`docs/publishing-the-skill.md`](docs/publishing-the-skill.md) documents how to open the upstream PR.

It has been executed end to end: [`examples/04-skill-portability`](examples/04-skill-portability/) is the captured run of an agent following the skill alone — no backend code in the loop — reaching the same root cause and **the same fourteen owners** as scenario 1. It was a warm run against an already-populated memory, and that example documents the caveats. Verifying it surfaced three real defects in the skill, all since fixed.

## Tests

```bash
cd backend
.venv/bin/ruff check src tests
.venv/bin/pytest
```

Unit tests mock the LLM and the MCP client; the scoring formula, the phase loop guards, the postmortem rendering and the orchestrator's failure policy are covered.

## License

Apache 2.0

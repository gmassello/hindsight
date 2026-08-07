# Hindsight

> **Your dashboard has been wrong since 03:00.** Hindsight already knows what broke it, who it hits, and writes the answer back into the catalog — so the next incident starts where this one ended.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](backend/pyproject.toml)

**[The memory loop, measured](examples/02-cold-vs-warm/) · [Five captured runs](examples/) · [The workflow as a portable Skill](.agents/skills/datahub-incident-triage/) · [Proposed upstream](https://github.com/datahub-project/datahub-skills/pull/110)**

The on-call agent for your data platform. When something breaks, Hindsight walks the DataHub lineage graph to compute who is affected, proposes a root cause backed by incidents you already solved, and writes the postmortem back into DataHub.

Built for the [Build with DataHub: The Agent Hackathon](https://datahub.devpost.com/) — track _Agents That Do Real Work_: agents that **read** DataHub to understand what is connected to what, **take action**, and **write the results back**.

## Every claim, and where to check it

Every number in this README comes from a file in this repository.

| Claim | Evidence |
| --- | --- |
| 13 MCP tools, read **and** mutation, multi-hop lineage in both directions | [`01-schema-drift/timeline.md`](examples/01-schema-drift/timeline.md) — 16 tool calls on a warm run, 20 consumers |
| Blast radius ranked by a deterministic formula, with the owner list to page | [`01-schema-drift/blast-radius.md`](examples/01-schema-drift/blast-radius.md) — total score 32.85, 14 deduplicated owners |
| Memory pays for itself: the same incident costs **29 tool calls cold and 17 warm** | [`02-cold-vs-warm/`](examples/02-cold-vs-warm/) |
| Five runs against a live catalog, four of them written by `--report` and the fifth transcribed by hand | [`examples/`](examples/) |
| The procedure runs with **no Hindsight code in the loop** — same URN, converging root cause, the same 14 owners | [`04-skill-portability/`](examples/04-skill-portability/) |
| The skill is proposed upstream to the official DataHub skills repo | [datahub-project/datahub-skills#110](https://github.com/datahub-project/datahub-skills/pull/110) |

## The closed loop

Every investigation makes the next one smarter, and that knowledge lives **inside DataHub**, not in a side database:

1. **Read** — multi-hop lineage traversal, schema inspection, query history, and the postmortems previous runs stored as DataHub documents.
2. **Act** — blast-radius scoring, ranked root-cause hypotheses with cited evidence, an action plan with a rationale per mutation.
3. **Write back** — the mutations below, applied to the catalog itself.

A later run even benefits from the write-back directly: an ancestor already tagged `hindsight-degraded` is evidence for the _upstream incident_ hypothesis — the system reads its own past actions.

### What gets written, and who inherits it

| Mutation | Where it lands in DataHub | Who inherits it |
| --- | --- | --- |
| `add_tags` `hindsight-degraded` | Tags on the broken asset | Anyone who searches or opens the asset — and the next Hindsight run, which reads the tag as evidence for the _upstream incident_ hypothesis |
| `add_tags` `hindsight-impacted` | Tags on the highest-scoring consumers | Downstream owners, through the search facets |
| `update_description` | An incident banner at the top of the asset description | Every consumer who opens the asset in the UI |
| `add_owners` | Ownership on an ungoverned asset in the incident path | The governance backlog, permanently |
| `set_domains` | Domain assignment | Same — implemented, but never triggered in the captured runs (see [Honest limits](#honest-limits)) |
| `save_document` | A postmortem document in the catalog | The **next** investigation's `recall` phase |

### vs. what DataHub already does

| DataHub gives you | Hindsight adds |
| --- | --- |
| Impact Analysis lists downstream entities | A ranking over them by a deterministic impact score, and the deduplicated owner list you actually have to page |
| A lineage graph you can walk by hand | An agent that walks it in both directions from a free-text alert and cites the URNs behind each hypothesis |
| Documents you can write | A postmortem the next investigation *retrieves and acts on* — memory, not documentation |

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

- **Deterministic phase pipeline, not a free ReAct loop.** The orchestrator picks the phase; the LLM interprets the results. Each phase emits timeline events and can be tested in isolation, and non-critical phases fail into "continue with partial information" instead of killing the run.
- **Per-phase toolsets.** Investigation phases (1–4) only ever see read tools; mutation tools exist only in `commit`/`learn`. The model cannot write while it should be reading.
- **Memory before investigation.** `recall` runs _before_ `impact`/`root_cause`, and what it retrieves becomes `investigation_hints` that direct where the root-cause search looks first. Memory steers the investigation instead of decorating it.
- **All math and writes are code.** The LLM reports facts; the score is a formula and the mutations are executed by code with an audit log. `impact(consumer) = type_weight × 1/(1+hops) × owner/criticality/domain multipliers`.
- **Human gate by default.** The agent can run autonomously (`--auto-approve`), but the default is a dry-run plan awaiting explicit approval. Every applied mutation is recorded in a JSONL audit log with timestamp, tool, URN, args and rationale.
- **Grounded mutations only.** `propose` sees the live mutation schemas and a whitelist of the URNs the investigation actually saw. A mutation it cannot ground in a real URN is dropped, not guessed.
- **MCP first, GraphQL fallback.** DataHub access goes through the official [`mcp-server-datahub`](https://github.com/acryldata/mcp-server-datahub) (stdio, mutations enabled). If a mutation tool is missing or fails, the same mutation is applied through the GMS GraphQL API.

## Quickstart

Prerequisites: Python 3.13+, [uv](https://docs.astral.sh/uv/), Node 20.19+ (for the web UI), a Gemini / Anthropic / Bedrock key, and Docker with at least 4 CPUs / 8 GB for the DataHub quickstart — on colima, `colima start --cpu 4 --memory 8`.

```bash
# 1. Local DataHub with sample lineage
uv tool install acryl-datahub
datahub docker quickstart                       # UI at http://localhost:9002 (datahub/datahub)
datahub datapack load showcase-ecommerce        # wait for the quickstart to report healthy first

# 2. Backend
cd backend
uv sync
cp ../.env.example .env                         # set GEMINI_API_KEY (or provider of choice)

# 3. Investigate an incident
.venv/bin/hindsight investigate \
  "orders table in order_entry_db is showing nulls in customer_id since 03:00 UTC today"
```

The CLI streams the timeline, renders the mutations as a dry-run diff, and applies them once you approve. Open the asset in the DataHub UI to see the tags, the incident banner and the document.

Run it twice: the second run's `recall` phase finds the postmortem the first run wrote and starts from its conclusions.

### Web UI

```bash
# terminal 1
cd backend && .venv/bin/hindsight serve         # FastAPI on :8000

# terminal 2
cd frontend && npm install && npm run dev       # Vite on http://localhost:5173
```

Single-page React app: submit an incident and watch the evidence timeline stream live over SSE while the panels fill in as each phase completes — resolved asset, "we've seen this before" (memory), blast radius ranked by impact score, root-cause hypotheses with confidence bars, and the proposed action plan rendered as a diff with **Approve / Reject** buttons (the human gate). After approval, each mutation shows its commit result and the postmortem reference.

If the API runs elsewhere, set `VITE_API_URL` in `frontend/.env` (defaults to `http://localhost:8000`).

### One-command bring-up (Docker)

With DataHub quickstart already running (step 1 above):

```bash
GEMINI_API_KEY=<your-key> docker compose up --build
```

Backend on `http://localhost:8000`, frontend on `http://localhost:5173`. The backend container reaches the host's DataHub through `host.docker.internal:8080`, so no compose changes are needed on macOS or Linux.

### API server

```bash
.venv/bin/hindsight serve                       # FastAPI on :8000
```

- `POST /investigations` `{"text": "..."}` → create
- `GET /investigations/{id}/stream` → SSE timeline, up to the human gate
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
| `HINDSIGHT_AUTO_APPROVE` | `false`                  | Skip the human gate                                                           |
| `HINDSIGHT_MAX_HOPS`     | `3`                      | Downstream lineage depth suggested to `impact` — a prompt hint, not a cut-off |
| `PHASE_MAX_TURNS`        | `12`                     | LLM turn budget per phase                                                     |
| `AUDIT_LOG_PATH`         | `var/audit-log.jsonl`    | Mutation audit log                                                            |

## Demo scenarios

`scenarios/scenarios.yaml` defines three reproducible scenarios; `examples/` holds five captured runs across four directories, each with its input, timeline, blast radius, postmortem and audit log. Four were written by `hindsight investigate ... --report <dir>`; the fifth is a run of the Skill alone, transcribed by hand:

1. [`01-schema-drift`](examples/01-schema-drift/) — a simulated upstream migration (`scenarios/break_schema.py`) drops the `customer_id` NOT NULL constraint; the agent traces the nulls to the Postgres ancestor a previous run had already tagged `hindsight-degraded`, tags the degraded and impacted assets, and saves the postmortem.
2. [`02-cold-vs-warm`](examples/02-cold-vs-warm/) ★ — the same incident twice. The cold run investigates from scratch (**29 DataHub tool calls**); the warm run's `recall` phase retrieves the postmortem the cold run just wrote and goes straight to the suspect ancestor (**17 calls, 41% fewer**). The two timelines sit side by side.
3. [`03-orphaned-asset`](examples/03-orphaned-asset/) — a stale table nobody owns and nobody consumes: besides the incident actions, the agent assigns `add_owners` to close the governance gap.
4. [`04-skill-portability`](examples/04-skill-portability/) — scenario 1 re-run by the Skill alone, with no Hindsight code in the loop. See below.

`scenarios/seed_incidents.py` loads six resolved historical postmortems into DataHub documents so `recall` has memory to work with.

## The workflow as a portable Skill

[`.agents/skills/datahub-incident-triage/`](.agents/skills/datahub-incident-triage/) distills this agent into an [Agent Skills](https://skills.sh) package: the same seven-step procedure — memory first, blast radius, ranked hypotheses, postmortem — as plain instructions, with no Python involved. Any Agent-Skills-compatible CLI with DataHub connected gets the behaviour without cloning this repo.

It is written against the same DataHub MCP tool names Hindsight uses, with `datahub` CLI fallbacks, and follows the conventions of [`datahub-project/datahub-skills`](https://github.com/datahub-project/datahub-skills).

It has been executed end to end: [`examples/04-skill-portability`](examples/04-skill-portability/) is the captured run of an agent following the skill alone, reaching **the same fourteen owners** as scenario 1 and naming that scenario's conclusion as its own second hypothesis. It was a warm run; the caveats and the three defects the verification surfaced are documented there.

## Notes from the build

Things that cost hours against a real DataHub and a real model, written down so they cost you minutes:

- **Gemini rejects `$ref`/`$defs` and unknown keys in function declarations.** All the normalization — ref inlining, key dropping, type uppercasing — lives in one place, `llm/gemini_provider.py::_clean_schema`, because splitting it across layers produces schemas that are valid at each step and invalid at the end. The trap inside the trap: a property legitimately *named* `title` under `properties` has to survive the same pass that drops `title` as schema metadata.
- **`MAX_TOKENS` is 16384 for a reason.** A `submit_*` payload carrying 30 consumers with full URNs blows past anything smaller, and the failure mode is the model going silent halfway through a JSON object rather than an explicit error.
- **`save_document` needs a `document_type` from a server-defined enum** (`Analysis`, `Note`, …). Read it from the live schema; a guessed value is a rejected write — `learn` reads the enum at runtime.
- **The MCP server hides the document tools entirely when the catalog has zero documents.** `recall` has to treat their absence as a cold start rather than an error, or the very first run against a fresh install fails on the phase that is supposed to find nothing.
- **`grep_documents` takes a `urns` argument** — it narrows an existing result set, it does not search the catalog. And `get_lineage_paths_between` takes `source_urn`/`target_urn`, not `upstream_urn`/`downstream_urn`. Both were guessed once and both cost a wasted turn — see [`examples/04-skill-portability`](examples/04-skill-portability/).
- **An agent that summarises its own postmortem quietly breaks the memory loop.** `grep_documents` matches literal text, so a prose summary of a blast radius is a document the next investigation cannot use. The postmortem has to carry every row, every owner URN and the largest hop count actually observed. This one was found by running the Skill end to end — see [`examples/04-skill-portability`](examples/04-skill-portability/).

## Honest limits

- **The phase prompts are not covered by tests.** Everything listed under [Tests](#tests) is; the prompts themselves are verified only by the captured runs in `examples/`.
- **Every number in `examples/` comes from a single run.** The cold-vs-warm delta (29 → 17 tool calls) is one pair against one catalog, not a repeated measurement with a variance.
- **Hindsight does not detect incidents.** It receives an alert and investigates it. Monitoring is one of the six things ruled out on purpose in [`docs/design.md`](docs/design.md) §3.
- **The API keeps investigations in an in-memory dict**, with no auth and no persistence. Restarting `hindsight serve` loses them. This is a demo, not a SaaS.
- **`set_domains` has never fired.** It is implemented, but the prompt forbids inventing a domain URN and no captured run retrieved one — domain URNs in this catalog are UUIDs. Scenario 3 therefore ships demonstrating the owner half of the governance gap.
- **Nothing here has been run against a second catalog** — one warehouse, one datapack (`showcase-ecommerce`).

## Project layout

```
backend/src/hindsight/
├── agent/
│   ├── orchestrator.py     # phase state machine, graceful degradation
│   ├── phase_agent.py      # generic LLM-with-tools loop (premature-submit guard, turn budget)
│   ├── context.py          # the Ctx phases mutate
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
├── api.ts, types.ts        # fetch client and the SSE contract
└── components/             # IncidentInput, Timeline, ResolvedAsset, RecallPanel,
                            # BlastRadius, HypothesesPanel, PlanPanel

scenarios/                  # seed_incidents.py, break_schema.py, scenarios.yaml
examples/                   # five captured runs; 04 is not in scenarios.yaml
.agents/skills/             # datahub-incident-triage: this workflow as a portable Agent Skill
.claude/skills →            # symlink to .agents/skills/, so Claude Code discovers them in this repo
AGENTS.md                   # agent instructions for this repo; CLAUDE.md just imports it
docker-compose.yml          # backend + frontend against an external DataHub quickstart
```

The frontend is deliberately dependency-free beyond React: native `EventSource` for streaming, plain CSS for the theme, no router or state library.

[`docs/design.md`](docs/design.md) is the design document frozen before implementation — useful for the *why*, but it describes what was planned. This file describes what was built; [`SUBMISSION.md`](SUBMISSION.md) tracks delivery status.

## Tests

```bash
cd backend
.venv/bin/ruff check src tests
.venv/bin/pytest
```

Unit tests mock the LLM and the MCP client; the scoring formula, the phase loop guards, the Gemini schema normalization, the postmortem rendering, the report writer and the orchestrator's failure policy are covered.

## License

Apache 2.0

# Configuration

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATAHUB_GMS_URL` | `http://localhost:8080` | GMS endpoint |
| `DATAHUB_GMS_TOKEN` | empty | PAT; empty works with the quickstart (auth disabled) |
| `DATAHUB_MCP_URL` | empty | Streamable-HTTP MCP endpoint (DataHub Cloud); empty spawns a local stdio server |
| `DATAHUB_MCP_COMMAND` | `uvx mcp-server-datahub` | Command for the stdio MCP server |
| `LLM_PROVIDER` | `gemini` | `gemini` \| `anthropic` \| `bedrock` |
| `GEMINI_API_KEY` | empty | Required when `LLM_PROVIDER=gemini` |
| `GEMINI_MODEL` | `gemini-flash-latest` | |
| `ANTHROPIC_API_KEY` | empty | Required when `LLM_PROVIDER=anthropic` |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-5-20250929` | |
| `AWS_REGION` | `us-east-1` | Bedrock only; credentials come from the usual `AWS_*` variables |
| `BEDROCK_MODEL_ID` | `us.anthropic.claude-sonnet-4-5-20250929-v1:0` | |
| `MAX_TOKENS` | `16384` | Per-response cap. Lowering it truncates `submit_*` payloads mid-JSON — see [notes from the build](notes-from-the-build.md) |
| `HINDSIGHT_AUTO_APPROVE` | `false` | Skip the human gate |
| `HINDSIGHT_MAX_HOPS` | `3` | Downstream lineage depth suggested to `impact` — a prompt hint, not a cut-off |
| `PHASE_MAX_TURNS` | `12` | LLM turn budget per phase |
| `AUDIT_LOG_PATH` | `var/audit-log.jsonl` | Mutation audit log |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated origins allowed by the API |

Defaults live in `backend/src/hindsight/config.py`; `.env.example` mirrors them.

## Repo layout

```
backend/src/hindsight/
├── agent/
│   ├── orchestrator.py     # phase state machine, graceful degradation
│   ├── phase_agent.py      # generic LLM-with-tools loop (premature-submit guard, turn budget)
│   ├── context.py          # the Ctx phases mutate
│   └── phases/             # intake, resolve, recall ★, impact, root_cause, propose, commit, learn ★
├── datahub/
│   ├── mcp_client.py       # MCP session (stdio or HTTP), read/write tool split via annotations
│   ├── graphql_fallback.py # GMS GraphQL: mutation fallback, and the channel `verify` reads through
│   └── lineage.py          # deterministic blast-radius scoring
├── llm/                    # provider-agnostic: gemini / anthropic / bedrock + structured output
├── memory/postmortem.py    # postmortem markdown rendering
├── safety/                 # dry-run rendering, JSONL audit log, verify.py
├── api/                    # FastAPI + SSE
└── cli.py                  # `hindsight investigate` / `replay` / `verify` / `serve`

frontend/src/
├── useInvestigation.ts     # all state + SSE lifecycle in one hook
├── App.tsx                 # layout: live timeline | progressive result panels
├── api.ts, types.ts        # fetch client and the SSE contract
└── components/             # IncidentInput, Timeline, ResolvedAsset, RecallPanel,
                            # BlastRadius, HypothesesPanel, PlanPanel

frontend/public/landing/    # the overview page, copied verbatim into dist/ by Vite
scenarios/                  # seed_incidents.py, break_schema.py, scenarios.yaml
examples/                   # five captured runs; 04 is not in scenarios.yaml
.agents/skills/             # datahub-incident-triage: this workflow as a portable Agent Skill
.claude/skills →            # symlink to .agents/skills/, so Claude Code discovers them
AGENTS.md                   # agent instructions for this repo; CLAUDE.md just imports it
docker-compose.yml          # backend + frontend against an external DataHub quickstart
```

The frontend is deliberately dependency-free beyond React: native `EventSource` for streaming, plain CSS for the theme, no router and no state library.

## Generated assets

Two files under `docs/` are compiled artifacts, not sources — never edit them by hand:

| Artifact | Source |
| --- | --- |
| `frontend/public/landing/index.html` | `docs/landing/Hindsight Landing.dc.html` |
| `docs/assets/{hero,memory,pipeline}.webp` | `docs/assets/README-assets-source.dc.html` |

Both sources carry run numbers that are hardcoded, not derived from `examples/`. After recapturing
a run, the numbers have to be updated in the source, the artifact regenerated, and `README.md`
edited to match — the artifacts fail silently otherwise.

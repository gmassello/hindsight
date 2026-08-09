# Submission checklist — Build with DataHub: The Agent Hackathon

Track: **Agents That Do Real Work** · Deadline: **Monday, August 10, 18:00 ART (5:00pm EDT)**

This file is the single source of truth for delivery status. For the reasoning behind the scope and the architecture, see the frozen design document in [`docs/design.md`](docs/design.md).

## Track requirements

The track rewards agents that **read** DataHub, **act**, and **write back**. All three must be visible in the demo.

| Verb | How Hindsight demonstrates it | Status |
|---|---|---|
| **Read** | Multi-hop lineage traversal (`search`, `get_entities`, `get_lineage`, `get_lineage_paths_between`, `list_schema_fields`, `get_dataset_queries`, `search_documents`, `grep_documents`) | ✅ Working |
| **Act** | Impact scoring, ranked root-cause hypotheses, action plan with human gate | ✅ Working |
| **Write back** | `add_tags`, `update_description`, `add_owners`, `save_document` — changes visible in DataHub UI. `set_domains` is implemented but has never fired in a captured run (see [README § Honest limits](README.md#honest-limits)) | ✅ Verified e2e |

> **Golden rule for the video**: if the demo doesn't end showing the DataHub UI with something the agent wrote, the track is not fulfilled.

## Deliverables

### Done

- [x] Backend: 8-phase orchestrator, CLI, FastAPI + SSE, tests
- [x] Frontend: SSE timeline, blast radius, memory panel, approval gate
- [x] End-to-end verification against local DataHub: cold run + approve (3 mutations + postmortem saved, see `examples/02-cold-vs-warm/cold/audit-log.json`), warm run recovering the previous postmortem, reject path
- [x] LICENSE: Apache 2.0
- [x] README: hero claim, claim→evidence table, architecture diagram, quickstart, design decisions, honest limits; the build notes moved to `docs/notes-from-the-build.md`
- [x] `scenarios/` — `seed_incidents.py` (6 historical postmortems), `break_schema.py` (verified live: break + reset), `scenarios.yaml`
- [x] `examples/` — **explicitly requested by the judges**: five runs across four directories, four of them written by `hindsight investigate ... --report <dir>`, each shipping its raw event stream (`events.json` + `state.json`) so `hindsight replay <dir>` reproduces the whole investigation with no DataHub and no API key
  - [x] `01-schema-drift/` — real run, 14 tool calls; with six seeded postmortems in memory, `recall` points at the Spark ingestion job and the agent converges there. It does **not** surface the planted `ALTER TABLE` note — the Skill run in `04-skill-portability` does, and that example says so
  - [x] `02-cold-vs-warm/` ★ — cold 20 vs. warm 15 tool calls (25% fewer); warm recall retrieves the cold run's postmortem and steers root_cause straight at the ingestion path. The example states the cost as well as the gain: the warm run swept 6 consumers against the cold run's 29
  - [x] `03-orphaned-asset/` — real run, 17 tool calls; applies `add_owners` on the unowned table, verified in DataHub. Recaptured after fixing four defects previously blamed on the model: `EntityRef` carried no `owners`/`domain`, the raw incident report never reached `propose`, `set_domains` was absent from the prompt conventions, and no phase knew the current date (fixed with an `InvestigationState.started_at` that `intake` resolves relative dates against, rather than patching the banner alone). The re-run uses the **same** `gemini-3.1-flash-lite` the caveat blamed — the proof it was never the model
- [x] `docker-compose.yml` — backend + frontend against external DataHub quickstart; smoke-tested
- [x] Open source Skill written: `.agents/skills/datahub-incident-triage/` — Agent Skills format, portable to any compatible CLI (Claude Code, Cursor, Codex, Gemini CLI, …). Passes the target repo's lint (prettier + markdownlint) and its tool names match the ones verified in the `examples/` runs
- [x] Skill verified end to end against live DataHub — an agent following only `SKILL.md`, with no backend code in the loop, reached a converging root cause and **the same 14 owner URNs, set for set**, as the cold Hindsight run of the same incident, in 9 investigation tool calls; applied 3 approved mutations and saved a postmortem that a re-search retrieved. Captured in [`examples/04-skill-portability/`](examples/04-skill-portability/), which also states the caveats (warm run against a cold comparison, audit log captured by hand). Verifying it surfaced three real defects in the skill, all fixed
- [x] Clean-clone test: repo cloned from GitHub into a fresh directory works following only the README — `uv sync`, `ruff`, `pytest` (30 passed), `hindsight serve` answering on `:8000`, `npm ci` + `npm run build`. Ran without DataHub, so it covers install/lint/test/build, not an end-to-end investigation (`examples/` already carries that evidence). Surfaced three defects, all fixed: Node missing from the prerequisites, no Docker resource floor for the quickstart, and `Settings.env_file` resolving relative to the cwd — which meant the `scenarios/` scripts, invoked from the repo root, silently ignored `backend/.env`
- [x] Open source Skill PR: [datahub-project/datahub-skills#110](https://github.com/datahub-project/datahub-skills/pull/110) — `feat: add datahub-incident-triage skill`. `Lint PR Title` green; the `Lint` workflow awaits first-time-contributor approval from a maintainer (pre-commit passes locally on the exact tree pushed). The PR link is enough, merge not required

- [x] Hosted demo reachable by URL — **required by the rules**: https://gmassello.github.io/hindsight/ — static replay of the captured runs on GitHub Pages, published by `.github/workflows/pages.yml`. Overview page alongside it at `/landing/`
- [x] CI on `main` and every PR: `.github/workflows/ci.yml` runs backend (`uv sync` + `ruff` + `pytest`) and frontend (`npm ci` + `npm run build` + `oxlint`) as parallel jobs

### Pending

- [ ] Video: 3 minutes, **public** — shot list and narration written before recording, in [`video/`](video); the build pipeline reports the measured length per beat
  - [x] Opens with the real on-call pain (first 20 seconds → applicability criterion)
  - [x] Shows scenario 2 (cold vs. warm) right before the closing moment
  - [x] Ends on the DataHub UI showing what the agent wrote — beat 6, after the warm run
  - [ ] Recorded, assembled, uploaded as public
- [ ] **Submission loaded on Devpost** — including the Skill PR link
- [ ] Feedback survey (US$50)

## Rubric mapping

All six criteria weigh equally; each needs an explicit answer.

| Criterion | Answer | Where the judges see it |
|---|---|---|
| Integration depth | 13 MCP tools (8 read, 5 mutation), multi-hop lineage, memory stored inside DataHub | Demo timeline + README claims table |
| Technical quality | Deterministic phase pipeline, per-phase toolset, dry-run, tests, GraphQL fallback | README "How it works" + `backend/tests/` |
| Originality | The memory loop: the system improves with use and the knowledge lives in DataHub | Scenario 2 in the video |
| Real-world applicability | Data on-call: concrete, expensive pain, backed by first-hand experience | First 20 seconds of the video |
| Delivery quality | `docker compose up` + README + `examples/` + hosted demo + CI on main and every PR; video pending | Everything |
| **Open source bonus** | `datahub-incident-triage` Skill proposed upstream | [datahub-skills#110](https://github.com/datahub-project/datahub-skills/pull/110) |

## Demo scenarios

Scenarios 1–3 are defined in `scenarios/scenarios.yaml` and reproducible from it; all four are captured in `examples/`.

- [x] **Scenario 1 — Schema drift**: root column breaks, agent ranks the 16 downstream consumers, walks upstream to the Spark ingestion job memory pointed it at, tags degraded and impacted assets, saves the postmortem. *Demonstrates multi-hop + write-back.*
- [x] **Scenario 2 — Cold vs. warm ★**: same incident twice; warm run retrieves the postmortem and reaches the root cause in fewer tool calls, measurably. *The visual proof of the thesis.*
- [x] **Scenario 3 — Governance gap**: agent detects an asset without owner in the incident path and proposes `add_owners`. *The agent improves the catalog, not just fights fires.* The run on record applies `add_owners` with `urn:li:corpGroup:b2fd91.ORG_DATA_PLATFORM`, verified written in DataHub. It ships demonstrating the owner half only — `set_domains` has never fired, see [README § Honest limits](README.md#honest-limits). Two notes that are *not* defects: the blast radius is 0 because `order_history` is a leaf nobody consumes, and the earlier "re-run with the full model" caveat was a misdiagnosis.
- [x] **Scenario 4 — Skill portability**: the same incident re-run by the Skill alone, no Hindsight code in the loop — converging root cause and the same 14 owner URNs as the cold Hindsight run. Not in `scenarios.yaml`; captured by hand in [`examples/04-skill-portability/`](examples/04-skill-portability/).

## Minimum viable vs. ideal

**Minimum viable (ships no matter what)**: CLI running all 8 phases, write-back with approval, scenario 2 cold-vs-warm working, `examples/`, README, video.

**Ideal**: all of the above + frontend with timeline and graph + hosted demo + all four scenarios + Skill PR.

## Final-day checklist (Sunday 9 / Monday 10)

- [x] README with architecture diagram and justified decisions
- [x] Skill PR opened — [datahub-project/datahub-skills#110](https://github.com/datahub-project/datahub-skills/pull/110)
- [x] Hosted demo live and reachable — https://gmassello.github.io/hindsight/
- [ ] Video recorded, edited, uploaded as **public**
- [ ] Devpost submission loaded — not "almost ready"
- [ ] Monday buffer: fresh-eyes review, finish before noon (deadline 18:00 ART)

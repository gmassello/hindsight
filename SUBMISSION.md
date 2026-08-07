# Submission checklist — Build with DataHub: The Agent Hackathon

Track: **Agents That Do Real Work** · Deadline: **Monday, August 10, 18:00 ART (5:00pm EDT)**

This file is the single source of truth for delivery status. For the reasoning behind the scope and the architecture, see the frozen design document in [`docs/design.md`](docs/design.md).

## Track requirements

The track rewards agents that **read** DataHub, **act**, and **write back**. All three must be visible in the demo.

| Verb | How Hindsight demonstrates it | Status |
|---|---|---|
| **Read** | Multi-hop lineage traversal (`search`, `get_entities`, `get_lineage`, `get_lineage_paths_between`, `list_schema_fields`, `get_dataset_queries`) | ✅ Working |
| **Act** | Impact scoring, ranked root-cause hypotheses, action plan with human gate | ✅ Working |
| **Write back** | `add_tags`, `update_description`, `add_owners`, `set_domains`, `save_document` — changes visible in DataHub UI | ✅ Verified e2e |

> **Golden rule for the video**: if the demo doesn't end showing the DataHub UI with something the agent wrote, the track is not fulfilled.

## Deliverables

### Done

- [x] Backend: 8-phase orchestrator, CLI, FastAPI + SSE, tests
- [x] Frontend: SSE timeline, blast radius, memory panel, approval gate
- [x] End-to-end verification against local DataHub: cold run + approve (5 mutations + postmortem saved), warm run recovering the previous postmortem, reject path
- [x] LICENSE: Apache 2.0
- [x] README exists — pending final pass (see below)

### Pending

- [x] `scenarios/` — `seed_incidents.py` (6 historical postmortems), `break_schema.py` (verified live: break + reset), `scenarios.yaml`
- [x] `examples/` — **explicitly requested by the judges** (captured with `hindsight investigate ... --report <dir>`)
  - [x] `01-schema-drift/` — real run, 16 tool calls; cites the planted upstream migration evidence
  - [x] `02-cold-vs-warm/` ★ — cold 29 vs. warm 17 tool calls (41% fewer); warm recall retrieves the cold run's postmortem and steers root_cause to the Postgres source
  - [x] `03-orphaned-asset/` — real run, 10 tool calls; applies `add_owners` on the unowned table and verifies it in DataHub. Recaptured after fixing four defects that the earlier caveat blamed on the model. The agent could not propose `add_owners` because the information never reached it: `EntityRef` carried no `owners`/`domain`, so with a legitimately empty blast radius the `propose` phase had no way to know the asset was ungoverned; the raw incident report — which names the owner group — was never passed either; `set_domains` was absent from the prompt conventions; and no phase knew the current date, so `detected_at` stayed `null` and the DataHub incident banner read `2023-10-27` in a 2026 run. All four are fixed — the date one by giving `InvestigationState` a `started_at` that `intake` resolves relative dates against, rather than patching the banner alone — and the re-run uses the **same** `gemini-3.1-flash-lite` that the caveat blamed, which is the proof it was never the model.
- [x] `docker-compose.yml` — backend + frontend against external DataHub quickstart; smoke-tested
- [x] README final pass: architecture diagram, quickstart, "Design decisions" section (deterministic phase pipeline, per-phase toolset, dry-run, human gate default, SDK fallback)
- [x] Open source Skill written: `.agents/skills/datahub-incident-triage/` — Agent Skills format, portable to any compatible CLI (Claude Code, Cursor, Codex, Gemini CLI, …). Passes the target repo's lint (prettier + markdownlint) and its tool names match the ones verified in the `examples/` runs
- [x] Skill verified end to end against live DataHub — an agent following only `SKILL.md`, with no backend code in the loop, reached the same root cause and the same 14 owners as scenario 1 in 9 investigation tool calls, applied 3 approved mutations and saved a postmortem that a re-search retrieved. Captured in [`examples/04-skill-portability/`](examples/04-skill-portability/), which also states the caveats (warm run, deeper memory than scenario 1, audit log captured by hand). Verifying it surfaced three real defects in the skill, all fixed
- [x] Clean-clone test: repo cloned from GitHub into a fresh directory works following only the README — `uv sync`, `ruff`, `pytest` (20 passed), `hindsight serve` answering on `:8000`, `npm ci` + `npm run build`. Ran without DataHub, so it covers install/lint/test/build, not an end-to-end investigation (`examples/` already carries that evidence). Surfaced three defects, all fixed: Node missing from the prerequisites, no Docker resource floor for the quickstart, and `Settings.env_file` resolving relative to the cwd — which meant the `scenarios/` scripts, invoked from the repo root, silently ignored `backend/.env`
- [ ] Video: 3 minutes, **public**, script written before recording with a timer per section
  - [ ] Opens with the real on-call pain (first 20 seconds → applicability criterion)
  - [ ] Shows scenario 2 (cold vs. warm) as the closing moment
  - [ ] Ends on the DataHub UI showing what the agent wrote
- [ ] Open source Skill PR: open `datahub-incident-triage` against `datahub-project/datahub-skills` — the skill is written, the step-by-step (fork, files to touch, lint, PR title) is in [`docs/publishing-the-skill.md`](docs/publishing-the-skill.md). The PR link is enough, merge not required
- [ ] **Submission loaded on Devpost** — including the Skill PR link
- [ ] Feedback survey (US$50)

## Rubric mapping

All six criteria weigh equally; each needs an explicit answer.

| Criterion | Answer | Where the judges see it |
|---|---|---|
| Integration depth | ~12 MCP tools, read **and** mutation, multi-hop lineage, memory stored inside DataHub | Demo timeline + README section |
| Technical quality | Deterministic phase pipeline, per-phase toolset, dry-run, tests, GraphQL fallback | README "Design decisions" + `backend/tests/` |
| Originality | The memory loop: the system improves with use and the knowledge lives in DataHub | Scenario 2 in the video |
| Real-world applicability | Data on-call: concrete, expensive pain, backed by first-hand experience | First 20 seconds of the video |
| Delivery quality | Hosted demo (or docker-compose + GIF) + video + README + `examples/` | Everything |
| **Open source bonus** | `datahub-incident-triage` Skill published in the registry | PR link in the submission |

## Demo scenarios

Each must be reproducible and deterministic. Defined in `scenarios/scenarios.yaml`, captured in `examples/`.

- [x] **Scenario 1 — Schema drift**: root column breaks, agent finds downstream consumers, traces cause 2 hops up, tags degraded assets, saves postmortem. *Demonstrates multi-hop + write-back.*
- [x] **Scenario 2 — Cold vs. warm ★**: same incident twice; warm run retrieves the postmortem and reaches the root cause in fewer tool calls, measurably. *The visual proof of the thesis.*
- [x] **Scenario 3 — Governance gap**: agent detects an asset without owner in the incident path and proposes `add_owners`. *The agent improves the catalog, not just fights fires.* The run on record applies `add_owners` with `urn:li:corpGroup:b2fd91.ORG_DATA_PLATFORM`, verified written in DataHub. `set_domains` is proposed only when the agent actually retrieves a domain URN during the investigation — the prompt forbids inventing one, and a domain URN in this catalog is a UUID. The captured run did not, so the scenario ships demonstrating the owner half. Two notes that are *not* defects: the blast radius is 0 because `order_history` is a leaf nobody consumes, and the earlier "re-run with the full model" caveat was a misdiagnosis — see below.

## Minimum viable vs. ideal

**Minimum viable (ships no matter what)**: CLI running all 8 phases, write-back with approval, scenario 2 cold-vs-warm working, `examples/`, README, video.

**Ideal**: all of the above + frontend with timeline and graph + hosted demo + all three scenarios + Skill PR.

## Final-day checklist (Sunday 9 / Monday 10)

- [ ] Video recorded, edited, uploaded as **public**
- [ ] README with architecture diagram and justified decisions
- [ ] Skill PR opened
- [ ] Devpost submission loaded — not "almost ready"
- [ ] Monday buffer: fresh-eyes review, finish before noon (deadline 18:00 ART)

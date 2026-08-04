# Submission checklist — Build with DataHub: The Agent Hackathon

Track: **Agents That Do Real Work** · Deadline: **Monday, August 10, 18:00 ART (5:00pm EDT)**

Source of truth for scope and rationale: `docs/plan-track-autonomous-agents.md`.

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
  - [x] `03-orphaned-asset/` — real run, 12 tool calls. Caveat: captured with `gemini-3.1-flash-lite` (free-tier fallback), which never proposes `add_owners`; re-run with the full model when quota resets. The cold run of scenario 2 already demonstrates `add_owners` on an unowned dashboard organically.
- [x] `docker-compose.yml` — backend + frontend against external DataHub quickstart; smoke-tested
- [ ] Clean-clone test: repo cloned into a fresh directory works following only the README
- [ ] README final pass: architecture diagram, quickstart, "Design decisions" section (deterministic phase pipeline, per-phase toolset, dry-run, human gate default, SDK fallback)
- [ ] Video: 3 minutes, **public**, script written before recording with a timer per section
  - [ ] Opens with the real on-call pain (first 20 seconds → applicability criterion)
  - [ ] Shows scenario 2 (cold vs. warm) as the closing moment
  - [ ] Ends on the DataHub UI showing what the agent wrote
- [ ] Open source Skill: `datahub-incident-triage` PR to `datahub-project/datahub-skills` (following the format of `datahub-search`, `datahub-lineage`, etc.) — the PR link is enough, merge not required
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

Each must be reproducible and deterministic.

- [ ] **Scenario 1 — Schema drift**: root column breaks, agent finds downstream consumers, traces cause 2 hops up, tags degraded assets, saves postmortem. *Demonstrates multi-hop + write-back.*
- [ ] **Scenario 2 — Cold vs. warm ★**: same incident twice; warm run retrieves the postmortem and reaches the root cause in fewer tool calls, measurably. *The visual proof of the thesis.*
- [ ] **Scenario 3 — Governance gap**: agent detects an asset without owner/domain in the incident path and proposes `add_owners` + `set_domains`. *The agent improves the catalog, not just fights fires.*

## Minimum viable vs. ideal

**Minimum viable (ships no matter what)**: CLI running all 8 phases, write-back with approval, scenario 2 cold-vs-warm working, `examples/`, README, video.

**Ideal**: all of the above + frontend with timeline and graph + hosted demo + all three scenarios + Skill PR.

## Final-day checklist (Sunday 9 / Monday 10)

- [ ] Video recorded, edited, uploaded as **public**
- [ ] README with architecture diagram and justified decisions
- [ ] Skill PR opened
- [ ] Devpost submission loaded — not "almost ready"
- [ ] Monday buffer: fresh-eyes review, finish before noon (deadline 18:00 ART)

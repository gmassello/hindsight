# Design document — Hindsight

## Build with DataHub: The Agent Hackathon · track "Agents That Do Real Work"

> Written 2 August 2026, before implementation started. Deadline: Monday 10 August, 18:00 ART.
>
> **This document is frozen.** It records the design as it was planned, not the system as it was
> built — some of what follows was superseded during implementation (the SDK fallback became a
> GraphQL fallback, memory retrieval became prompts inside the `recall` phase, the Agent Context
> Kit was never used). For the architecture as it actually exists, read `README.md`. For delivery
> status, read `SUBMISSION.md`.

---

## 1. What this track rewards

The official definition of the track, word for word:

> Autonomous agents that **read DataHub to understand what is connected to what, take action, and
> write the results back**.

Three verbs, all three required. Most entrants will manage the first (read) and perhaps the second
(reason), but **very few will write back**, because that requires enabling the mutation tools and
designing a safety layer. That gap is the competitive opening.

Translated into design decisions:

| Verb           | What the demo has to show                      | Tools                                                                                                             |
| -------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Read**       | Multi-hop lineage traversal, not a flat search | `search`, `get_entities`, `get_lineage`, `get_lineage_paths_between`, `list_schema_fields`, `get_dataset_queries` |
| **Act**        | A decision with consequences, not a summary    | Impact scoring, ranked root-cause hypotheses, action plan                                                         |
| **Write back** | DataHub's state changes and shows it in its UI | `add_tags`, `update_description`, `add_owners`, `set_domains`, `save_document`                                    |

**Rule of thumb for the video**: if the demo does not end on the DataHub UI showing something the
agent wrote, the track has not been satisfied.

---

## 2. The thesis

> **Hindsight is the on-call engineer for your data platform. When something breaks, it walks the
> DataHub lineage graph to compute who is affected, proposes a root cause backed by incidents you
> already solved, and writes the postmortem back into DataHub — so the next diagnosis starts where
> this one ended.**

The closed loop is the argument. This is not a chatbot over metadata: it is a system that gets
smarter with every use, and that improvement lives **inside DataHub**, not in a side database. That
detail is what turns the integration from "deep" into "inevitable".

### Why this angle wins

With roughly 764 registrants, the distribution of projects is predictable: a lot of text-to-SQL
(the Analytics Agent already exists and is open source, so it is the obvious path), several
chat-with-your-catalog entries, some documentation generators. Almost all of them will be
**read-only**.

This project differs on three axes at once:

1. **It writes back** — the track asks for it explicitly and few will do it
2. **It uses the graph as a graph** — multi-hop traversal with scoring, not a single `search`
3. **It has memory** — the system accumulates knowledge, and that knowledge stays in DataHub

---

## 3. Scope: what is in and what is out

With eight days of evenings, the main risk is not technical, it is scope. This is what will **not**
be built:

| Out of scope                              | Why                                                           |
| ----------------------------------------- | ------------------------------------------------------------- |
| Executing SQL against a real warehouse    | Not needed, and it adds an enormous failure surface           |
| PagerDuty / Slack / Jira integration      | Sounds good in a pitch, adds nothing to the rubric            |
| Multi-user authentication                 | This is a demo, not a SaaS                                    |
| Automatic incident detection (monitoring) | The agent receives the alert, it does not generate it         |
| Fine-tuning or custom embeddings          | DataHub's `search_documents` already provides semantic recall |
| Multi-warehouse support                   | One environment, `showcase-ecommerce`                         |

What is in, in non-negotiable priority order:

1. An agent that diagnoses end to end over real lineage
2. Write-back to DataHub with human approval
3. Postmortem memory that feeds the next diagnosis
4. A UI with a streaming evidence timeline
5. Three reproducible scenarios plus an `examples/` directory

If day 7 runs late, item 4 is the first to go. A CLI with well-formatted output scores the same.

---

## 4. Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  FRONTEND  React + Vite + TS               [reused from Recall]  │
│  ┌────────────────┐ ┌──────────────┐ ┌────────────────────────┐  │
│  │ Evidence       │ │ Blast radius │ │ "We've seen this"      │  │
│  │ timeline (SSE) │ │ graph        │ │ panel (prior incidents)│  │
│  └────────────────┘ └──────────────┘ └────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Proposed action plan  →  [ Approve ] [ Reject ]           │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬────────────────────────────────────┘
                              │ SSE
┌─────────────────────────────▼────────────────────────────────────┐
│  BACKEND  FastAPI                          [reused from Recall]  │
│                                                                   │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │  PHASE ORCHESTRATOR  (deterministic state machine)       │    │
│   │  intake → resolve → recall → impact → root_cause →       │    │
│   │           → propose → [ human gate ] → commit → learn    │    │
│   └───────────────────────┬─────────────────────────────────┘    │
│                           │                                       │
│   ┌───────────────────────▼──────────┐  ┌──────────────────────┐ │
│   │  PROVIDER-AGNOSTIC LLM LAYER     │  │  WRITE LAYER         │ │
│   │  Anthropic / Gemini / Bedrock    │  │  dry-run + audit log │ │
│   │        [reused from Recall]      │  │        [new]         │ │
│   └───────────────────────┬──────────┘  └──────────┬───────────┘ │
└───────────────────────────┼────────────────────────┼─────────────┘
                            │                        │
                  ┌─────────▼────────────────────────▼──────────┐
                  │      DATAHUB MCP CLIENT          [new]       │
                  │      + Python SDK fallback                   │
                  └─────────────────────┬───────────────────────┘
                                        │
                  ┌─────────────────────▼───────────────────────┐
                  │  DataHub (self-hosted, quickstart)          │
                  │  MCP at http://<gms-host>:8080/mcp          │
                  │  Datapack: showcase-ecommerce (1,049 ent.)  │
                  └─────────────────────────────────────────────┘
```

### Key design decision: a phase pipeline, not a loose ReAct loop

A free ReAct loop looks more impressive on paper but it is a lottery in a recorded demo: sometimes
the model does not call the right tool, sometimes it wanders, sometimes it takes 90 seconds. The
deliverable includes a three-minute video, which means determinism is a requirement.

The right architecture is a **deterministic state machine with an LLM inside each phase**. The
orchestrator decides _which_ phase runs and _which_ tools are available in it; the LLM decides _how_
to interpret the results. What this buys:

- Each phase emits a timeline event → the streaming looks impressive and stays predictable
- Each phase can be tested in isolation
- When a phase fails, the run degrades gracefully instead of collapsing
- The judges see a considered architecture rather than a `while True` with tools

This decision belongs in the README. The "technical quality" criterion is won with justified
decisions, not with lines of code.

---

## 5. The agent, phase by phase

### Phase 0 — `intake`

Input: free text. _"fct_orders has been showing nulls in customer_id since 03:00 UTC"_, or an alert
JSON from dbt / Monte Carlo / Airflow.

Output: a structured `Incident` (Pydantic) with `raw_text`, `mentioned_assets[]`, `symptom_type`
(nulls / freshness / schema / volume / failure) and `detected_at`.

No tools. Just an LLM with structured output. Cheap and fast.

### Phase 1 — `resolve`

Tools: `search` → `get_entities`

Resolve the names mentioned in natural language into **concrete DataHub URNs**. When there is
ambiguity (two tables with similar names), the agent picks the one with the strongest signal — more
downstream consumers, has an owner, has a domain — and **records the ambiguity in the timeline**.
That bit of epistemic honesty is what impresses judges.

Output: `resolved_asset: EntityRef` plus `alternatives[]`.

### Phase 2 — `recall` ★ (the differentiator)

Tools: `search_documents`, `grep_documents`

**This phase belongs here and not at the end, and that is the most important product decision in
the project.**

The obvious approach would be to investigate first and show "similar incidents" as a decoration on
the side. The correct approach is to **search memory before investigating, and let what comes back
steer the investigation**. If this same dataset broke three months ago because of an upstream schema
change in `raw_customers`, the agent should go look at `raw_customers` _first_.

Output: `prior_incidents[]` with similarity and prior resolution, plus **`investigation_hints[]`** —
the URNs and cause types memory suggests checking first.

In the timeline this reads as: _"Found 2 similar incidents. Checking `raw_customers` first because
it was the origin back in March."_ That is the moment for the video.

### Phase 3 — `impact`

Tools: `get_lineage` (DOWNSTREAM, 3+ hops)

Walk the graph downstream and compute the blast radius. Proposed formula, defensible and simple:

```
impact(consumer) = type_weight × hop_decay × criticality_multiplier

  type_weight:          Dashboard = 3 · MLModel/MLFeature/MLFeatureTable = 3
                        Chart = 2 · DataJob = 2 · Dataset = 1
  hop_decay:            1 / (1 + hops)
  multipliers:          ×1.5 if it has an assigned owner
                        ×2.0 if it carries a Tier1 / PII glossary term
                        ×1.3 if it belongs to a domain

total_impact = Σ impact(consumer)
```

Output: `blast_radius` with the ranked list of affected consumers, the total, and **the owners to
notify** (grouped, deduplicated). "Who needs to be told" is an actionable answer; "what broke" is
just information.

### Phase 4 — `root_cause`

Tools: `get_lineage` (UPSTREAM), `get_lineage_paths_between`, `list_schema_fields`,
`get_dataset_queries`, `get_entities`

Guided by the `investigation_hints` from phase 2. Produces ranked hypotheses, each with explicit
evidence:

| Hypothesis                      | How it is detected                                                                                             |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Upstream schema drift**       | `list_schema_fields` over the ancestors: a column that vanished, changed type, or became nullable              |
| **Transformation query change** | `get_dataset_queries` on the asset and its direct parents                                                      |
| **Active upstream incident**    | An ancestor already carries the `hindsight-degraded` tag (written by a previous run — the system reads itself) |
| **Propagation path**            | `get_lineage_paths_between` the broken asset and the suspect ancestor: shows the exact route                   |
| **Historical precedent**        | Phase 2's memory has already seen this pattern                                                                 |

Output: `hypotheses[]` ordered by confidence, each with `evidence[]` citing concrete URNs. **Never a
single answer delivered with certainty** — an honest on-call gives ranked hypotheses, and that is
exactly what a senior engineer values.

### Phase 5 — `propose`

No DataHub tools. The LLM assembles an **action plan** in dry-run mode:

```json
{
  "mutations": [
    {
      "tool": "add_tags",
      "urn": "urn:li:dataset:(...,fct_orders,PROD)",
      "args": { "tags": ["hindsight-degraded"] },
      "rationale": "Asset with a confirmed active incident"
    },
    {
      "tool": "add_tags",
      "urn": "urn:li:dashboard:(...,exec_revenue)",
      "args": { "tags": ["hindsight-impacted"] },
      "rationale": "Consumer 2 hops out, impact score 4.5"
    },
    {
      "tool": "update_description",
      "urn": "...",
      "args": {
        "description": "⚠️ Active incident since 2026-08-08 03:00 UTC..."
      },
      "rationale": "Warn anyone who opens the asset in the UI"
    },
    {
      "tool": "add_owners",
      "urn": "...",
      "args": { "owners": ["urn:li:corpuser:data-platform"] },
      "rationale": "Critical asset with no owner — governance gap detected"
    }
  ],
  "document": {
    "tool": "save_document",
    "title": "Incident 2026-08-08: nulls in fct_orders.customer_id"
  }
}
```

Rendered as a readable diff. **Nothing executes yet.**

### Phase 6 — `commit` (behind the human gate)

Tools: `add_tags`, `update_description`, `add_owners`, `set_domains`

Runs **only after explicit approval**. Every mutation is recorded in an audit log with timestamp,
tool, URN, arguments and rationale. The log is exposed in the UI and saved under `examples/`.

> **`--auto-approve` mode**: implement it but leave it off by default, and document why. "The agent
> can run autonomously, but the default is to ask permission" is a mature design stance that judges
> from a governance company will value. It is their own pitch.

### Phase 7 — `learn` ★ (closes the loop)

Tool: `save_document`

Saves the structured postmortem as a DataHub document. That document is what phase 2 of the **next**
run will retrieve.

Postmortem schema:

```markdown
# Incident {id} — {title}

**Asset**: {urn}
**Detected**: {timestamp}
**Symptom**: {type} — {description}
**Status**: {active | resolved}

## Blast radius

{N} affected consumers within {M} hops. Score: {score}
Owners notified: {list}

| Asset | Type | Hops | Score |
| ----- | ---- | ---- | ----- |

## Root cause hypotheses

1. {hypothesis} — confidence {X}%
   Evidence: {cited urns}

## Resolution

{filled in by the human, or inferred}

## Detection signals

{what to watch for to catch it earlier next time}

## Tags

{symptom}, {platform}, {cause type}
```

**The closing moment of the video**: run the same scenario twice. The first time the agent
investigates from scratch and takes a while. The second time, phase 2 retrieves the postmortem it
wrote itself and goes straight to the point. _That_ is "agents that do real work".

---

## 6. Technical setup

### Local DataHub

```bash
# Prerequisites: Docker + Docker Compose v2 + Python 3.10+
# Docker needs: 2 CPUs, 8GB RAM, 2GB swap, 13GB disk

pip install acryl-datahub          # current version: 1.6.0.x
datahub docker quickstart          # UI at http://localhost:9002 (datahub/datahub)

datahub init --username datahub --password datahub
datahub datapack load showcase-ecommerce
```

Rescue commands: `datahub docker quickstart --stop` · `datahub docker nuke` (full reset) ·
`datahub docker quickstart --backup`

### MCP server with mutations enabled

The self-hosted endpoint is `http://<gms-host>:8080/mcp`. **The mutation tools are off by default**
and without them the track is not satisfied:

```bash
TOOLS_IS_MUTATION_ENABLED=true      # ← ESSENTIAL, defaults to false
TOOLS_IS_USER_ENABLED=true          # for add_owners
SEMANTIC_SEARCH_ENABLED=true        # ← significantly improves the memory phase
TOOL_RESPONSE_TOKEN_LIMIT=80000     # raise it if lineage comes back truncated
```

Verify this on **day 0**. If mutations do not work in the installed version, plan B is writing
through the Python SDK directly (`acryl-datahub`), which still qualifies although it is less
elegant.

### Agent Context Kit

```bash
pip install datahub-agent-context   # requires Python 3.10+ and a PAT
```

Exposes tool builders for LangChain and Google ADK. The `include_mutations` flag controls whether
the write tools enter the toolset — pass `True` for phases 6 and 7, `False` for phases 1 to 4.
**Splitting the toolset per phase stops the model from writing when it should be reading**, and it
is an engineering detail worth mentioning in the README.

### Project environment variables

Follow the official Analytics Agent convention, so the judges recognise the pattern:

```bash
DATAHUB_GMS_URL=http://localhost:8080
DATAHUB_GMS_TOKEN=<personal access token>
LLM_PROVIDER=anthropic              # anthropic | openai | google | bedrock
LLM_MODEL=<primary model>
HINDSIGHT_AUTO_APPROVE=false        # human gate on by default
HINDSIGHT_MAX_HOPS=3
```

---

## 7. Repository layout

```
hindsight/
├── LICENSE                      # Apache 2.0 — from the first commit
├── README.md                    # architecture, quickstart, design decisions
├── docker-compose.yml           # one command brings everything up (deploy plan B)
├── .env.example
│
├── backend/
│   ├── src/hindsight/
│   │   ├── agent/
│   │   │   ├── orchestrator.py      # the state machine
│   │   │   └── phases/
│   │   │       ├── intake.py
│   │   │       ├── resolve.py
│   │   │       ├── recall.py        # ★
│   │   │       ├── impact.py
│   │   │       ├── root_cause.py
│   │   │       ├── propose.py
│   │   │       ├── commit.py
│   │   │       └── learn.py         # ★
│   │   ├── datahub/
│   │   │   ├── mcp_client.py        # MCP client
│   │   │   ├── sdk_fallback.py      # plan B if MCP fails
│   │   │   └── lineage.py           # traversal + scoring
│   │   ├── llm/                     # provider-agnostic layer [from Recall]
│   │   ├── memory/
│   │   │   ├── postmortem.py        # schema + serialisation
│   │   │   └── retrieval.py
│   │   ├── safety/
│   │   │   ├── dry_run.py
│   │   │   └── audit_log.py
│   │   └── api/                     # FastAPI + SSE [from Recall]
│   └── tests/
│
├── frontend/                    # React + Vite + TS [from Recall]
│
├── scenarios/
│   ├── seed_incidents.py        # seeds 6-8 historical postmortems
│   ├── break_schema.py          # breaks the environment deterministically
│   └── scenarios.yaml
│
└── examples/                    # ← EXPLICITLY REQUESTED BY THE JUDGES
    ├── 01-schema-drift/
    │   ├── input.txt
    │   ├── timeline.md          # full investigation trace
    │   ├── blast-radius.md
    │   ├── postmortem.md
    │   └── audit-log.json
    ├── 02-cold-vs-warm/         # ★ the same incident without and with memory
    └── 03-orphaned-asset/
```

---

## 8. The three demo scenarios

> **Day 0 task**: open `http://localhost:9002` after loading `showcase-ecommerce`, map the real
> graph and write down the concrete URNs. The names below are illustrative until confirmed against
> the datapack.

### Scenario 1 — Schema drift (the base case)

A column changes type or becomes nullable in a root table. The agent resolves the asset, finds 12
downstream consumers including two dashboards, traces the cause 2 hops up with
`get_lineage_paths_between`, tags what is degraded and saves the postmortem.

_Demonstrates_: multi-hop traversal + write-back.

### Scenario 2 — Cold vs. warm ★ (the scenario that wins)

**The same incident, run twice.**

- **Cold run**: empty memory. The agent investigates blind, explores three lineage branches, reaches
  the root cause after 9 tool calls.
- **Warm run**: phase 2 retrieves the postmortem from the previous run, goes straight to the suspect
  ancestor, confirms in 3 calls.

Put the two traces side by side in `examples/02-cold-vs-warm/`. **It is the visual proof of the
thesis** and no other project will have anything like it.

### Scenario 3 — Governance gap (the bonus)

The agent detects that a critical asset on the incident path has neither owner nor domain assigned,
and proposes `add_owners` + `set_domains` on top of the incident actions.

_Demonstrates_: the agent does not only fight fires, it improves the catalog. That is DataHub's own
commercial pitch, made by this project.

---

## 9. Schedule with "done when" criteria

### Sunday 2 — Setup · 3 h

- Start `datahub docker quickstart` **first**, it is the slowest step
- Load `showcase-ecommerce` and map the graph by hand in the UI
- **Verify `TOOLS_IS_MUTATION_ENABLED=true`** and try an `add_tags` from Claude Code or Cursor
- Repository created with an Apache 2.0 `LICENSE`
- Register on Devpost + Slack `#agent-hackathon`

> **Done when**: a dataset has been tagged from an MCP client and the tag shows up in the DataHub UI.

### Monday 3 — Skeleton · 4 h

- Port the LLM layer and the FastAPI + SSE setup from Recall
- `mcp_client.py` with the read tools
- Phases `intake` and `resolve`

> **Done when**: free text goes in through the console and the correct URN comes out.

### Tuesday 4 — Impact · 4 h

- Multi-hop downstream `get_lineage`
- Scoring formula implemented
- Grouping of owners to notify

> **Done when**: for a known asset it returns the ranked list of consumers with scores, and the
> numbers make sense at a glance.

### Wednesday 5 — Memory · 5 h ★

- Postmortem schema + `save_document`
- `search_documents` / `grep_documents` in the `recall` phase
- `seed_incidents.py` with 6–8 plausible historical postmortems
- `investigation_hints` feeding the `root_cause` phase

> **Done when**: the cold-vs-warm scenario shows a measurable difference in tool call count.
> **This is the critical day. If anything slips, it must not be this.**

### Thursday 6 — Root cause + write-back · 4 h

- Ranked hypotheses with cited evidence
- `propose` / `commit` phases with dry-run, human gate and audit log

> **Done when**: a plan approved from the console produces changes visible in the DataHub UI.

### Friday 7 — Frontend · 4 h

- SSE timeline, blast radius graph, similar-incidents panel, approval button

> **Done when**: someone else understands what happened just by looking at the screen.

### Saturday 8 — Scenarios and deploy · 6 h

- The three scenarios, reproducible and deterministic
- `examples/` complete
- Public deploy, or a one-command `docker-compose up` with a GIF in the README

> **Done when**: the repository cloned into a clean directory works following only the README.

### Sunday 9 — Delivery · 5 h

- Three-minute video recorded, edited and uploaded **as public**
- README with architecture diagram and justified decisions
- Open source Skill PR
- **Submission loaded on Devpost**

> **Done when**: the submission is loaded. Not "almost ready".

### Monday 10 — Buffer · 2 h

- Fresh-eyes review, adjustments, feedback survey (US$50)
- **Deadline 18:00 ART. Finish before noon.**

---

## 10. Mapping to the rubric

The six criteria weigh equally. Each one needs an explicit answer.

| Criterion                | The answer                                                                            | Where the judges see it              |
| ------------------------ | ------------------------------------------------------------------------------------- | ------------------------------------ |
| Integration depth        | ~12 MCP tools, read **and** mutation, multi-hop lineage, memory stored inside DataHub | Demo timeline + README section       |
| Technical quality        | Deterministic phase pipeline, per-phase toolset, dry-run, tests, SDK fallback         | README "Design decisions" + `tests/` |
| Originality              | The memory loop: the system improves with use and the knowledge lives in DataHub      | Scenario 2 in the video              |
| Real-world applicability | Data on-call: concrete, expensive pain, backed by first-hand experience               | The first 20 seconds of the video    |
| Delivery quality         | Hosted demo + video + README + `examples/` + GIF                                      | Everything                           |
| **Open source bonus**    | `datahub-incident-triage` Skill published in the registry                             | PR link in the submission            |

### The open source contribution

It is the cheapest item in the whole rubric and the one fewest people will do. Publish a Skill in
`datahub-project/datahub-skills` following the format of the existing ones (`datahub-search`,
`datahub-lineage`, `datahub-enrich`, `datahub-quality`):

**`datahub-incident-triage`** — the recipe for any Agent Skills-compatible agent to triage a data
incident: which tools to call, in what order, how to read the lineage, how to write the postmortem.

It is the project distilled into a reusable artifact, and it is exactly the kind of contribution a
maintainer wants to receive. Open the PR on Sunday even if it is not merged — the PR link is enough.

---

## 11. Risks and fallbacks

| Risk                                       | Early signal                          | Fallback                                                                |
| ------------------------------------------ | ------------------------------------- | ----------------------------------------------------------------------- |
| The mutation tools do not work             | Day 0, the test `add_tags` fails      | Write through the Python SDK (`acryl-datahub`). Still qualifies         |
| The datapack lineage is flatter than hoped | Day 0, looking at the graph in the UI | Ingest extra synthetic lineage with the SDK, or switch datapacks        |
| Lineage responses come back truncated      | Day 2, context full                   | Raise `TOOL_RESPONSE_TOKEN_LIMIT`, paginate the traversal               |
| `search_documents` retrieves poorly        | Day 3, the recall phase returns noise | Enable `SEMANTIC_SEARCH_ENABLED=true`; if that is not enough, own index |
| The frontend eats the weekend              | Friday night with no timeline         | Cut it. A CLI with rich output scores the same                          |
| The hosted demo does not happen            | Saturday                              | `docker-compose up` + a GIF in the README. Documented from the start    |
| The video runs long or confusing           | Sunday                                | Script written **before** recording, with a timer per section           |

### Minimum deliverable vs. ideal

Define this now, in the cold, so it does not get renegotiated at 2am on Sunday:

**Minimum viable** (ships no matter what): a CLI running the 8 phases, write-back to DataHub with
approval, the cold-vs-warm scenario working, `examples/`, README, video.

**Ideal**: all of the above plus a frontend with timeline and graph, a hosted demo, all three
scenarios, and the Skill PR.

The minimum viable is already a competitive project. Everything else is margin.

---

## 12. The first three commands

```bash
# 1. This takes a while. Start it now and carry on with the rest while it downloads.
pip install acryl-datahub && datahub docker quickstart

# 2. Data with real lineage to work against
datahub init --username datahub --password datahub
datahub datapack load showcase-ecommerce

# 3. The repository, with the right licence from commit one
mkdir hindsight && cd hindsight && git init
curl -sL https://www.apache.org/licenses/LICENSE-2.0.txt -o LICENSE
```

Then: open `http://localhost:9002`, find a dataset with several downstream consumers, and note its
URN. That one is the protagonist of the demo.

---

## Links

**Hackathon** — [Devpost](https://datahub.devpost.com/) · [Rules](https://datahub.devpost.com/rules) · [Resources](https://datahub.devpost.com/resources) · [Announcement blog](https://datahub.com/blog/build-with-datahub-agent-hackathon/) · Slack `#agent-hackathon`

**Docs** — [Quickstart](https://docs.datahub.com/docs/quickstart) · [MCP Server](https://docs.datahub.com/docs/features/feature-guides/mcp) · [Agent Context Kit](https://docs.datahub.com/docs/dev-guides/agent-context/agent-context) · [Analytics Agent](https://docs.datahub.com/docs/features/feature-guides/analytics-agent) · [Autonomous Data Agents](https://datahub.com/blog/building-autonomous-data-agents/) · [Skills Registry](https://datahub.com/blog/datahub-open-source-skills-registry/)

**Repos** — [DataHub Core](https://github.com/datahub-project/datahub) · [Skills](https://github.com/datahub-project/datahub-skills) · [Analytics Agent](https://github.com/datahub-project/analytics-agent) · [MCP Server](https://github.com/acryldata/mcp-server-datahub)

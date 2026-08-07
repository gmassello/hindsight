# datahub-incident-triage

On-call triage for data incidents — diagnose a broken asset by walking DataHub lineage, then write the conclusion back into the catalog.

## What it does

- **Parses** a free-text incident report or an alert JSON (dbt, Airflow, Monte Carlo) into a structured incident and resolves the names to concrete DataHub URNs
- **Searches memory first** — past postmortems stored as DataHub documents steer the investigation before it starts, instead of decorating it afterwards
- **Computes the blast radius** downstream with a deterministic impact score, and reports the deduplicated list of owners to notify
- **Ranks root-cause hypotheses** with cited evidence URNs: schema drift upstream, query change, an already-degraded ancestor, a source-side issue, or a historical precedent
- **Proposes the write-back as a dry run** — incident tags, an incident banner on the asset, owners for governance gaps — and applies it **only after explicit approval**
- **Saves the postmortem** back to DataHub, which is what the next investigation retrieves

## Install

Every Agent Skills-compatible agent reads skills from its own directory, so installing means copying this folder to the right place:

| Agent                                     | Path                |
| ----------------------------------------- | ------------------- |
| Claude Code                               | `.claude/skills/`   |
| Cursor, GitHub Copilot, Codex, Gemini CLI | `.agents/skills/`   |
| Windsurf                                  | `.windsurf/skills/` |

```bash
cp -r .agents/skills/datahub-incident-triage <your-project>/.claude/skills/
```

Or let the [Skills CLI](https://github.com/vercel-labs/skills) detect the agent for you:

```bash
npx skills add gmassello/hindsight
```

In this repository the skill lives at `.agents/skills/` and `.claude/skills` is a symlink to it, so Claude Code picks this one up as `/datahub-incident-triage` — and any skill added later — without copying anything.

## Usage

```
> orders in order_entry_db is showing NULL values in customer_id since 03:00 UTC
> the exec revenue dashboard numbers are wrong, figure out what broke
> triage this: {"asset": "analytics.order_history", "check": "freshness", "status": "fail"}
> /datahub-incident-triage order_details is stale since yesterday
```

## Files

| File                                          | Purpose                                            |
| --------------------------------------------- | -------------------------------------------------- |
| `SKILL.md`                                    | Main skill instructions — the seven-step workflow  |
| `references/impact-scoring-reference.md`      | The deterministic blast-radius formula and weights |
| `references/root-cause-patterns-reference.md` | The five cause patterns and how to detect each     |
| `templates/postmortem.template.md`            | The postmortem format that memory can retrieve     |

## Requirements

Read-only triage works against any DataHub deployment. The write-back steps need the MCP mutation tools enabled (`TOOLS_IS_MUTATION_ENABLED=true`, plus `TOOLS_IS_USER_ENABLED=true` for owner assignment), or a `datahub` CLI with permission to run GraphQL mutations.

The memory loop needs the DataHub document tools (`search_documents`, `grep_documents`, `save_document`). If they are absent the skill still works — it treats it as a cold start.

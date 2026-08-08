import asyncio
import json
from collections.abc import AsyncIterator

from hindsight.agent.context import Ctx
from hindsight.llm.structured import complete_structured
from hindsight.models import ActionPlan, TimelineEvent

SYSTEM = """You are Hindsight, the on-call agent for a data platform. The investigation is done.
Build the action plan: the DataHub mutations that leave the catalog reflecting this incident.
Nothing you propose is executed yet; a human reviews the plan first.

Available mutation tools and their exact argument schemas:
{schemas}

The investigation reached this verdict: {verdict}

If the verdict is exonerated, there is no incident and the catalog must not be marked as if there
were one. Return zero mutations: no tags, no banner, no owners, no domain. Put in rationale one or
two sentences on what was checked and why nothing is being written, and still give
postmortem_title: the finding that this alert was not an incident is worth remembering. Proposing
nothing is the correct answer here, not a failure.

Otherwise, apply these conventions:
- Tag the broken asset with urn:li:tag:hindsight-degraded.
- Tag affected downstream consumers (the highest-impact ones) with urn:li:tag:hindsight-impacted.
- update_description on the broken asset: prepend a short warning dated with detected_at
  (or started_at if the report gives none), plus symptom and status, so anyone opening the
  asset in the DataHub UI sees it (operation must be one of the values allowed above).
- Resolved asset with empty owners: propose add_owners. Empty domain: propose set_domains.
- Owner (urn:li:corpGroup/corpuser) and domain (urn:li:domain) URNs must be copied verbatim
  from the investigation — a sibling asset usually carries the right one. Never invent or
  complete one; with no URN to cite, skip the mutation.
- Mutation targets (entity_urn / entity_urns) may only come from this list; a mutation
  targeting anything else is dropped:
{urns}

Each mutation needs a one-line rationale. Also give postmortem_title: a short, specific title
for the postmortem document."""

MAX_REPORT_CHARS = 4000


def _seen_urns(ctx: Ctx) -> set[str]:
    state = ctx.state
    urns: set[str] = set()
    if state.resolution:
        urns.add(state.resolution.resolved_asset.urn)
        urns.update(a.urn for a in state.resolution.alternatives)
    if state.blast_radius:
        urns.update(a.urn for a in state.blast_radius.impacted)
    for h in state.hypotheses:
        urns.update(h.evidence_urns)
    return {u for u in urns if u}


def _summary(ctx: Ctx) -> str:
    state = ctx.state
    return json.dumps(
        {
            "incident_report": state.input_text[:MAX_REPORT_CHARS],
            "started_at": state.started_at,
            "incident": state.incident.model_dump() if state.incident else None,
            "resolved_asset": state.resolution.model_dump() if state.resolution else None,
            "blast_radius": state.blast_radius.model_dump() if state.blast_radius else None,
            "verdict": state.verdict,
            "hypotheses": [h.model_dump() for h in state.hypotheses],
        },
        ensure_ascii=False,
        default=str,
    )


async def run(ctx: Ctx) -> AsyncIterator[TimelineEvent]:
    yield TimelineEvent(phase="propose", kind="info", message="Building action plan (dry-run)")
    tool_names = ["add_tags", "update_description", "add_owners", "set_domains"]
    schemas = {spec.name: spec.input_schema for spec in ctx.datahub.specs(tool_names)}
    urns = _seen_urns(ctx)
    system = SYSTEM.format(
        schemas=json.dumps(schemas, ensure_ascii=False),
        urns="\n".join(f"- {u}" for u in sorted(urns)),
        verdict=ctx.state.verdict,
    )
    plan = await asyncio.to_thread(complete_structured, system, _summary(ctx), ActionPlan)

    exonerated = ctx.state.verdict == "exonerated"
    allowed: set[str] = set() if exonerated else urns
    kept = [m for m in plan.mutations if m.targets() and all(t in allowed for t in m.targets())]
    if len(kept) < len(plan.mutations):
        reason = (
            "the verdict is exonerated, so the catalog is not marked"
            if exonerated
            else "they reference URNs never seen during the investigation"
        )
        yield TimelineEvent(
            phase="propose",
            kind="warning",
            message=f"Dropped {len(plan.mutations) - len(kept)} mutation(s): {reason}",
        )
    plan.mutations = kept
    ctx.state.plan = plan

    detail = (
        "No action proposed: this alert is not an incident. Only the finding is saved."
        if exonerated
        else f"Action plan ready: {len(kept)} mutation(s) + 1 postmortem document."
    )
    yield TimelineEvent(
        phase="propose",
        kind="result",
        message=f"{detail} Awaiting human approval.",
        data=plan.model_dump(),
    )

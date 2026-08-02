from collections.abc import AsyncIterator

from hindsight.agent.context import Ctx
from hindsight.agent.phase_agent import run_phase_agent
from hindsight.models import RecallResult, TimelineEvent

SYSTEM = """You are Hindsight, the on-call agent for a data platform. Before investigating this
incident, search the incident memory: past postmortems stored as documents in DataHub.

Procedure:
1. Use search_documents with the symptom and the asset name (try a couple of phrasings).
2. Use grep_documents to find postmortems that mention the exact asset name or URN.
3. Call submit_recall with what you found:
   - prior_incidents: past incidents genuinely similar to this one (same asset, same symptom,
     or same root-cause pattern). Include how each was resolved.
   - investigation_hints: concrete URNs and cause types the investigation should check FIRST,
     based on what caused similar incidents before. This is the whole point: memory directs
     the investigation.
A postmortem written by a previous Hindsight run about this same asset or symptom is the
STRONGEST possible match — include it with similarity high and turn its hypotheses and cited
URNs into investigation_hints. Never exclude a document for describing "the same incident".
If nothing similar exists, submit empty lists. Never invent precedents."""

TOOLS = ["search_documents", "grep_documents"]


async def run(ctx: Ctx) -> AsyncIterator[TimelineEvent]:
    if not any(ctx.datahub.has(t) for t in TOOLS):
        ctx.state.recall = RecallResult()
        yield TimelineEvent(
            phase="recall",
            kind="result",
            message="Document tools not exposed by this DataHub MCP server "
            "(memory is empty, or documents are disabled). Skipping memory recall.",
        )
        return

    incident = ctx.state.incident
    asset = ctx.state.resolution.resolved_asset
    prompt = (
        f"Current incident: {incident.symptom_type} — {incident.symptom_description}\n"
        f"Affected asset: {asset.name} ({asset.urn})"
    )
    async for kind, item in run_phase_agent(
        phase="recall",
        system=SYSTEM,
        prompt=prompt,
        datahub=ctx.datahub,
        tool_names=TOOLS,
        result_cls=RecallResult,
        submit_name="submit_recall",
        submit_description="Submit similar prior incidents and investigation hints from memory.",
    ):
        if kind == "event":
            yield item
            continue
        ctx.state.recall = item
        if not item.prior_incidents:
            yield TimelineEvent(
                phase="recall",
                kind="result",
                message="No similar prior incidents in memory. Investigating from scratch.",
            )
            return
        hints = "; ".join(
            f"check {h.urn or h.cause_type} first ({h.reason})"
            for h in item.investigation_hints
        )
        yield TimelineEvent(
            phase="recall",
            kind="result",
            message=(
                f"Found {len(item.prior_incidents)} similar prior incident(s). "
                + (f"Memory suggests: {hints}" if hints else "")
            ),
            data=item.model_dump(),
        )

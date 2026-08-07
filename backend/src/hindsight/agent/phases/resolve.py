from collections.abc import AsyncIterator

from hindsight.agent.context import Ctx
from hindsight.agent.phase_agent import run_phase_agent
from hindsight.models import ResolveResult, TimelineEvent

SYSTEM = """You are Hindsight, the on-call agent for a data platform, working against DataHub.
Resolve the asset names mentioned in an incident to concrete DataHub URNs.

Procedure:
1. Use search with each mentioned asset name.
2. If several candidates match, use get_entities to compare them and pick the one with the
   strongest signal: more downstream consumers, has an owner, has a domain, PROD environment.
   It takes a list of urns, so fetch every candidate in one call.
3. Call submit_resolution with the chosen asset. If there was any ambiguity, list the
   discarded candidates in alternatives and explain the choice in ambiguity_note.
   Being explicit about ambiguity is required; silently guessing is not acceptable.
   For the chosen asset and every alternative, report from get_entities:
   - owners: owner URNs, empty list if none.
   - domain: the domain URN, empty string if none.
   Include siblings among the alternatives: one often carries the ownership and domain
   the chosen asset lacks."""

TOOLS = ["search", "get_entities"]


async def run(ctx: Ctx) -> AsyncIterator[TimelineEvent]:
    incident = ctx.state.incident
    prompt = (
        f"Incident: {incident.symptom_description}\n"
        f"Symptom type: {incident.symptom_type}\n"
        f"Mentioned assets: {', '.join(incident.mentioned_assets) or '(none, infer from text)'}\n"
        f"Raw report: {ctx.state.input_text}"
    )
    async for kind, item in run_phase_agent(
        phase="resolve",
        system=SYSTEM,
        prompt=prompt,
        datahub=ctx.datahub,
        tool_names=TOOLS,
        result_cls=ResolveResult,
        submit_name="submit_resolution",
        submit_description="Submit the resolved DataHub asset for this incident.",
    ):
        if kind == "event":
            yield item
            continue
        ctx.state.resolution = item
        if item.ambiguity_note:
            yield TimelineEvent(
                phase="resolve", kind="warning", message=f"Ambiguity: {item.ambiguity_note}"
            )
        yield TimelineEvent(
            phase="resolve",
            kind="result",
            message=f"Resolved to {item.resolved_asset.urn}",
            data=item.model_dump(),
        )

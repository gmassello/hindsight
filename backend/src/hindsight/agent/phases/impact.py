from collections.abc import AsyncIterator

from hindsight.agent.context import Ctx
from hindsight.agent.phase_agent import run_phase_agent
from hindsight.config import settings
from hindsight.datahub.lineage import build_blast_radius
from hindsight.models import ConsumersReport, TimelineEvent

SYSTEM = """You are Hindsight, the on-call agent for a data platform. Map the blast radius of
this incident: every downstream consumer of the broken asset.

Procedure:
1. Use get_lineage on the asset URN with upstream=false and max_hops={max_hops} to walk the
   graph downstream. Paginate with offset if results are truncated.
2. Use get_entities on the consumers you found to check their type, owners, domain, and
   glossary terms (Tier1 / PII terms mean the asset is critical).
3. Call submit_consumers with the downstream consumers found (cap at the 30 most
   important if there are more — prefer dashboards, ML assets and owned datasets):
   - hops: distance from the broken asset (1 = direct consumer).
   - owners: owner URNs, empty list if none.
   - is_critical: true if it carries Tier1/PII glossary terms or is clearly business-critical.
   - in_domain: true if it belongs to a domain.
Do not score or rank anything; report facts only. The scoring is computed deterministically."""

TOOLS = ["get_lineage", "get_entities"]


async def run(ctx: Ctx) -> AsyncIterator[TimelineEvent]:
    asset = ctx.state.resolution.resolved_asset
    prompt = f"Broken asset: {asset.name} ({asset.urn}). Map its downstream blast radius."
    async for kind, item in run_phase_agent(
        phase="impact",
        system=SYSTEM.format(max_hops=settings.hindsight_max_hops),
        prompt=prompt,
        datahub=ctx.datahub,
        tool_names=TOOLS,
        result_cls=ConsumersReport,
        submit_name="submit_consumers",
        submit_description="Submit every downstream consumer of the broken asset.",
    ):
        if kind == "event":
            yield item
            continue
        blast = build_blast_radius(item.consumers)
        ctx.state.blast_radius = blast
        owners = ", ".join(blast.owners_to_notify) or "none found"
        yield TimelineEvent(
            phase="impact",
            kind="result",
            message=(
                f"{len(blast.impacted)} downstream consumers affected, "
                f"total impact score {blast.total_score}. Owners to notify: {owners}"
            ),
            data=blast.model_dump(),
        )

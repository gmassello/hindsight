import json
from collections.abc import AsyncIterator

from pydantic import BaseModel, Field

from hindsight.agent.context import Ctx
from hindsight.agent.phase_agent import run_phase_agent
from hindsight.models import Hypothesis, TimelineEvent

SYSTEM = """You are Hindsight, the on-call agent for a data platform. Find the most likely root
cause of this incident by investigating the upstream lineage in DataHub.

Procedure:
1. If the memory provided investigation hints, check those URNs and cause types FIRST.
2. Use get_lineage with upstream=true to find the ancestors of the broken asset.
3. Look for evidence of each cause pattern:
   - schema_drift_upstream: list_schema_fields on ancestors — column removed, type changed,
     or newly nullable.
   - query_change: get_dataset_queries on the asset and its direct parents.
   - upstream_incident: an ancestor already tagged hindsight-degraded (written by a previous
     Hindsight run — the system reads its own past actions).
   - propagation path: get_lineage_paths_between the broken asset and a suspect ancestor.
4. Call submit_hypotheses with hypotheses ranked by confidence (highest first). Each one must
   cite concrete evidence and the URNs it is based on. Never give a single answer with false
   certainty: an honest on-call gives ranked hypotheses. If you found nothing conclusive,
   say so with low confidence."""

TOOLS = [
    "get_lineage",
    "get_lineage_paths_between",
    "list_schema_fields",
    "get_dataset_queries",
    "get_entities",
]


class HypothesesReport(BaseModel):
    hypotheses: list[Hypothesis] = Field(default_factory=list)


async def run(ctx: Ctx) -> AsyncIterator[TimelineEvent]:
    state = ctx.state
    asset = state.resolution.resolved_asset
    hints = state.recall.investigation_hints if state.recall else []
    hint_text = (
        json.dumps([h.model_dump() for h in hints], ensure_ascii=False)
        if hints
        else "(none — cold start, investigate from scratch)"
    )
    prompt = (
        f"Broken asset: {asset.name} ({asset.urn})\n"
        f"Symptom: {state.incident.symptom_type} — {state.incident.symptom_description}\n"
        f"Investigation hints from memory: {hint_text}"
    )
    async for kind, item in run_phase_agent(
        phase="root_cause",
        system=SYSTEM,
        prompt=prompt,
        datahub=ctx.datahub,
        tool_names=TOOLS,
        result_cls=HypothesesReport,
        submit_name="submit_hypotheses",
        submit_description="Submit root cause hypotheses ranked by confidence.",
    ):
        if kind == "event":
            yield item
            continue
        hypotheses = sorted(item.hypotheses, key=lambda h: h.confidence, reverse=True)
        state.hypotheses = hypotheses
        if not hypotheses:
            yield TimelineEvent(
                phase="root_cause", kind="warning", message="No hypotheses produced"
            )
            return
        top = hypotheses[0]
        yield TimelineEvent(
            phase="root_cause",
            kind="result",
            message=(
                f"{len(hypotheses)} hypothesis(es). Top: {top.statement} "
                f"(confidence {round(top.confidence * 100)}%)"
            ),
            data={"hypotheses": [h.model_dump() for h in hypotheses]},
        )

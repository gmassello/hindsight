import asyncio
from collections.abc import AsyncIterator

from hindsight.agent.context import Ctx
from hindsight.llm.structured import complete_structured
from hindsight.models import Incident, TimelineEvent

SYSTEM = """You are Hindsight, the on-call agent for a data platform. You receive a free-text
incident report (or an alert JSON from dbt, Airflow, Monte Carlo, etc.) and must parse it
into a structured incident.

Rules:
- mentioned_assets: every table, dataset, dashboard or pipeline name mentioned, verbatim.
- symptom_type: nulls | freshness | schema | volume | failure | other.
- symptom_description: one sentence, factual, no speculation about causes.
- detected_at: copy timestamps verbatim if present. Resolve relative ones ("yesterday",
  "03:00 UTC today") against today's date, given below. Null only if the report says nothing
  about when it started."""


async def run(ctx: Ctx) -> AsyncIterator[TimelineEvent]:
    yield TimelineEvent(phase="intake", kind="info", message="Parsing incident report")
    prompt = f"Today is {ctx.state.started_at}.\n\n{ctx.state.input_text}"
    incident = await asyncio.to_thread(complete_structured, SYSTEM, prompt, Incident)
    ctx.state.incident = incident
    assets = ", ".join(incident.mentioned_assets) or "none"
    yield TimelineEvent(
        phase="intake",
        kind="result",
        message=f"Symptom: {incident.symptom_type}. Assets mentioned: {assets}",
        data=incident.model_dump(),
    )

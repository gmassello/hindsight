import logging
from collections.abc import AsyncIterator, Callable

from hindsight.agent.context import Ctx
from hindsight.agent.phases import (
    commit,
    impact,
    intake,
    learn,
    propose,
    recall,
    resolve,
    root_cause,
)
from hindsight.models import TimelineEvent

log = logging.getLogger(__name__)

Phase = tuple[str, str, Callable, bool]

INVESTIGATE_PHASES: list[Phase] = [
    ("intake", "Understanding the incident report", intake.run, True),
    ("resolve", "Resolving asset names to DataHub URNs", resolve.run, True),
    ("recall", "Searching incident memory in DataHub", recall.run, False),
    ("impact", "Walking downstream lineage to compute blast radius", impact.run, False),
    ("root_cause", "Investigating upstream lineage for the root cause", root_cause.run, False),
    ("propose", "Drafting the action plan", propose.run, True),
]

COMMIT_PHASES: list[Phase] = [
    ("commit", "Writing approved changes back to DataHub", commit.run, True),
    ("learn", "Saving the postmortem to DataHub memory", learn.run, False),
]


async def _run_phases(ctx: Ctx, phases: list[Phase]) -> AsyncIterator[TimelineEvent]:
    for name, description, run, critical in phases:
        yield TimelineEvent(phase=name, kind="start", message=description)
        try:
            async for event in run(ctx):
                if event.kind == "tool_call":
                    ctx.state.tool_calls += 1
                yield event
        except Exception as exc:
            log.exception("Phase %s failed", name)
            yield TimelineEvent(phase=name, kind="error", message=f"Phase failed: {exc}")
            if critical:
                ctx.state.status = "failed"
                return
            yield TimelineEvent(
                phase=name, kind="warning", message="Continuing with partial information"
            )


async def investigate(ctx: Ctx) -> AsyncIterator[TimelineEvent]:
    ctx.state.status = "investigating"
    async for event in _run_phases(ctx, INVESTIGATE_PHASES):
        yield event
    if ctx.state.status != "failed":
        ctx.state.status = "awaiting_approval"


async def commit_and_learn(ctx: Ctx) -> AsyncIterator[TimelineEvent]:
    ctx.state.status = "committing"
    async for event in _run_phases(ctx, COMMIT_PHASES):
        yield event
    if ctx.state.status != "failed":
        ctx.state.status = "done"

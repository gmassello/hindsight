import asyncio
import logging
from collections.abc import AsyncIterator

from hindsight.agent.context import Ctx
from hindsight.config import settings
from hindsight.datahub import graphql_fallback
from hindsight.models import CommitRecord, Mutation, TimelineEvent
from hindsight.safety import audit_log

log = logging.getLogger(__name__)


async def _execute(ctx: Ctx, m: Mutation) -> str:
    via = "graphql"
    if ctx.datahub.has(m.tool):
        try:
            await ctx.datahub.call(m.tool, m.args)
            return "mcp"
        except Exception as exc:
            log.warning("MCP %s failed, falling back to GraphQL: %s", m.tool, exc)
            via = "graphql-fallback"
    await asyncio.to_thread(graphql_fallback.run_fallback, m.tool, m.args, m.urn)
    return via


async def run(ctx: Ctx) -> AsyncIterator[TimelineEvent]:
    plan = ctx.state.plan
    ensured_tags: set[str] = set()
    for m in plan.mutations:
        record = CommitRecord(tool=m.tool, urn=m.urn, args=m.args, rationale=m.rationale)
        try:
            if m.tool == "add_tags":
                for tag in m.args.get("tag_urns", []):
                    if tag not in ensured_tags:
                        try:
                            await asyncio.to_thread(graphql_fallback.ensure_tag, tag)
                        except Exception as exc:
                            log.warning("ensure_tag(%s) failed, continuing: %s", tag, exc)
                        ensured_tags.add(tag)
            record.via = await _execute(ctx, m)
            yield TimelineEvent(
                phase="commit",
                kind="info",
                message=f"Applied {m.tool} via {record.via}: {m.rationale}",
                data=record.model_dump(),
            )
        except Exception as exc:
            record.ok = False
            record.error = str(exc)
            yield TimelineEvent(
                phase="commit",
                kind="error",
                message=f"{m.tool} failed: {str(exc)[:200]}",
                data=record.model_dump(),
            )
        ctx.state.committed.append(record)
        audit_log.record(ctx.state.id, record)

    applied = sum(1 for r in ctx.state.committed if r.ok)
    yield TimelineEvent(
        phase="commit",
        kind="result",
        message=f"{applied}/{len(plan.mutations)} mutations applied to DataHub. "
        f"Audit log: {settings.audit_log_path}",
    )

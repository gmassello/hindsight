from collections.abc import AsyncIterator

from hindsight.agent.context import Ctx
from hindsight.memory.postmortem import postmortem_title, render_markdown, save_document_args
from hindsight.models import TimelineEvent


async def run(ctx: Ctx) -> AsyncIterator[TimelineEvent]:
    state = ctx.state
    if not ctx.datahub.has("save_document"):
        yield TimelineEvent(
            phase="learn",
            kind="error",
            message="save_document is not exposed by this DataHub MCP server; "
            "the postmortem could not be stored",
        )
        return
    title = postmortem_title(state)
    content = render_markdown(state, title)
    schema = ctx.datahub.tools["save_document"].input_schema
    related = state.resolution.resolved_asset.urn if state.resolution else None
    args = save_document_args(schema, title, content, related)
    result = await ctx.datahub.call("save_document", args)
    ref = ""
    if isinstance(result, dict):
        ref = result.get("urn") or result.get("id") or ""
    state.postmortem_ref = ref or None
    yield TimelineEvent(
        phase="learn",
        kind="result",
        message=f'Postmortem "{title}" saved to DataHub. '
        "The next investigation of a similar incident will start from it.",
        data={"reference": state.postmortem_ref},
    )

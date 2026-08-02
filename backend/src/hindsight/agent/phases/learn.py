from collections.abc import AsyncIterator

from hindsight.agent.context import Ctx
from hindsight.memory.postmortem import default_title, render_markdown
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
    title = (state.plan.postmortem_title if state.plan else "") or default_title(state)
    content = render_markdown(state, title)
    args: dict = {"title": title, "content": content}
    schema = ctx.datahub.tools["save_document"].input_schema
    properties = schema.get("properties", {})
    if "related_assets" in properties and state.resolution:
        args["related_assets"] = [state.resolution.resolved_asset.urn]
    doc_type = properties.get("document_type", {})
    allowed = doc_type.get("enum") or [
        option["const"] for option in doc_type.get("anyOf", []) if option.get("const")
    ]
    if allowed:
        args["document_type"] = "Analysis" if "Analysis" in allowed else allowed[0]
    result = await ctx.datahub.call("save_document", args)
    ref = ""
    if isinstance(result, dict):
        ref = result.get("urn") or result.get("id") or ""
    state.postmortem_ref = ref or title
    yield TimelineEvent(
        phase="learn",
        kind="result",
        message=f'Postmortem "{title}" saved to DataHub. '
        "The next investigation of a similar incident will start from it.",
        data={"reference": state.postmortem_ref},
    )

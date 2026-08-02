import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel, ValidationError

from hindsight.config import settings
from hindsight.datahub.mcp_client import DataHubMCP
from hindsight.llm.base import Message, ToolResult
from hindsight.llm.registry import get_llm
from hindsight.llm.structured import submit_spec
from hindsight.models import TimelineEvent

log = logging.getLogger(__name__)

NO_CONTENT = "(no content)"

SUBMIT_REQUEST = (
    "You did not call any tool. If you already have what you need, call {submit}; "
    "if you are missing context, use the available read tools first."
)

PREMATURE_SUBMIT = (
    "You called {submit} in the same turn as other tools, so you have not seen "
    "their results yet. The submission was discarded. Review the results and call "
    "{submit} again."
)

LAST_CHANCE = (
    "You are almost out of turns. Stop investigating and call {submit} NOW with the "
    "evidence you already have. A partial answer with honest confidence beats no answer."
)


class PhaseFailed(RuntimeError):
    pass


async def run_phase_agent(
    phase: str,
    system: str,
    prompt: str,
    datahub: DataHubMCP,
    tool_names: list[str],
    result_cls: type[BaseModel],
    submit_name: str,
    submit_description: str,
) -> AsyncIterator[tuple[str, Any]]:
    llm = get_llm()
    tools = datahub.specs(tool_names)
    missing = [n for n in tool_names if not datahub.has(n)]
    if missing:
        yield (
            "event",
            TimelineEvent(
                phase=phase,
                kind="warning",
                message=f"Tools not exposed by this DataHub MCP server: {', '.join(missing)}",
            ),
        )
    if not tools:
        tools = datahub.read_tools()
        yield (
            "event",
            TimelineEvent(
                phase=phase,
                kind="warning",
                message="Falling back to all read tools exposed by the server",
            ),
        )
    terminal = submit_spec(result_cls, submit_name, submit_description)
    messages = [Message(role="user", text=prompt)]
    result: BaseModel | None = None

    for turn_index in range(settings.phase_max_turns):
        turn = await asyncio.to_thread(llm.converse, system, messages, [*tools, terminal])
        if turn.truncated:
            log.warning("Provider truncated turn at max_tokens=%s", settings.max_tokens)
        if not turn.tool_uses:
            messages.append(Message(role="assistant", text=turn.text or NO_CONTENT))
            messages.append(
                Message(role="user", text=SUBMIT_REQUEST.format(submit=submit_name))
            )
            if turn_index == settings.phase_max_turns - 2:
                messages.append(
                    Message(role="user", text=LAST_CHANCE.format(submit=submit_name))
                )
            continue

        messages.append(
            Message(role="assistant", text=turn.text or None, tool_uses=turn.tool_uses)
        )
        results: list[ToolResult] = []
        has_other = any(u.name != submit_name for u in turn.tool_uses)
        for use in turn.tool_uses:
            if use.name == submit_name:
                if has_other:
                    results.append(
                        ToolResult(
                            id=use.id,
                            content=PREMATURE_SUBMIT.format(submit=submit_name),
                            is_error=True,
                        )
                    )
                    continue
                try:
                    result = result_cls.model_validate(use.args)
                except ValidationError as exc:
                    results.append(
                        ToolResult(id=use.id, content=f"Invalid arguments: {exc}", is_error=True)
                    )
                continue
            try:
                returned = await datahub.call(use.name, use.args)
                is_error = False
            except Exception as exc:
                log.warning("Tool %s failed: %s", use.name, exc)
                returned, is_error = f"error: {exc}", True
            results.append(ToolResult(id=use.id, content=returned, is_error=is_error))
            yield (
                "event",
                TimelineEvent(
                    phase=phase,
                    kind="tool_call",
                    message=f"{use.name}({_summarize(use.args)})",
                    data={"tool": use.name, "args": use.args, "error": is_error},
                ),
            )

        if result is not None:
            yield ("result", result)
            return
        messages.append(Message(role="user", tool_results=results))
        if turn_index == settings.phase_max_turns - 2:
            messages.append(Message(role="user", text=LAST_CHANCE.format(submit=submit_name)))

    raise PhaseFailed(
        f"Phase {phase} did not reach {submit_name} within {settings.phase_max_turns} turns"
    )


def _summarize(args: dict[str, Any]) -> str:
    parts = []
    for key, value in args.items():
        text = str(value)
        parts.append(f"{key}={text[:60]}")
    return ", ".join(parts)

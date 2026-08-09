from typing import Any

import anthropic

from hindsight.config import settings
from hindsight.llm.base import Message, ToolSpec, ToolUse, Turn, as_text, merge_user_turns


def _to_anthropic_message(message: Message) -> dict[str, Any]:
    content: list[dict[str, Any]] = []
    for result in message.tool_results:
        content.append(
            {
                "type": "tool_result",
                "tool_use_id": result.id,
                "content": as_text(result.content),
                "is_error": result.is_error,
            }
        )
    if message.text:
        content.append({"type": "text", "text": message.text})
    for use in message.tool_uses:
        content.append({"type": "tool_use", "id": use.id, "name": use.name, "input": use.args})
    return {"role": message.role, "content": content}


class AnthropicProvider:
    def __init__(self) -> None:
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required with LLM_PROVIDER=anthropic")
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.anthropic_model

    def converse(
        self, system: str, messages: list[Message], tools: list[ToolSpec]
    ) -> Turn:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=settings.max_tokens,
            system=system,
            messages=[_to_anthropic_message(m) for m in merge_user_turns(messages)],
            tools=[
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                }
                for tool in tools
            ],
        )
        turn = Turn(truncated=response.stop_reason == "max_tokens")
        for block in response.content:
            if block.type == "text":
                turn.text += block.text
            elif block.type == "tool_use":
                turn.tool_uses.append(
                    ToolUse(id=block.id, name=block.name, args=dict(block.input))
                )
        return turn

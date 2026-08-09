import json
from dataclasses import dataclass, field
from typing import Any, Protocol


def as_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False, default=str)


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass
class ToolUse:
    id: str
    name: str
    args: dict[str, Any]
    signature: Any = None


@dataclass
class ToolResult:
    id: str
    content: Any
    is_error: bool = False


@dataclass
class Message:
    role: str
    text: str | None = None
    tool_uses: list[ToolUse] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)


def merge_user_turns(messages: list[Message]) -> list[Message]:
    merged: list[Message] = []
    for message in messages:
        previous = merged[-1] if merged else None
        if previous is not None and previous.role == message.role == "user":
            merged[-1] = Message(
                role="user",
                text="\n\n".join(t for t in (previous.text, message.text) if t) or None,
                tool_uses=[*previous.tool_uses, *message.tool_uses],
                tool_results=[*previous.tool_results, *message.tool_results],
            )
        else:
            merged.append(message)
    return merged


@dataclass
class Turn:
    text: str = ""
    tool_uses: list[ToolUse] = field(default_factory=list)
    truncated: bool = False


class LLMProvider(Protocol):
    def converse(
        self, system: str, messages: list[Message], tools: list[ToolSpec]
    ) -> Turn: ...

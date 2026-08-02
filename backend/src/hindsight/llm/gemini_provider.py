from typing import Any

from google import genai
from google.genai import types

from hindsight.config import settings
from hindsight.llm.base import Message, ToolSpec, ToolUse, Turn

_ROLE = {"assistant": "model"}
_DROP_KEYS = {"default", "title", "additionalProperties", "$schema"}


def _inline_refs(node: Any, defs: dict[str, Any]) -> Any:
    if isinstance(node, dict):
        if "$ref" in node:
            name = node["$ref"].split("/")[-1]
            merged = {**defs.get(name, {}), **{k: v for k, v in node.items() if k != "$ref"}}
            return _inline_refs(merged, defs)
        return {k: _inline_refs(v, defs) for k, v in node.items() if k != "$defs"}
    if isinstance(node, list):
        return [_inline_refs(item, defs) for item in node]
    return node


def _drop_and_uppercase(node: Any) -> Any:
    if isinstance(node, dict):
        out: dict[str, Any] = {}
        for key, value in node.items():
            if key == "properties" and isinstance(value, dict):
                out[key] = {name: _drop_and_uppercase(sub) for name, sub in value.items()}
            elif key in _DROP_KEYS:
                continue
            elif key == "type" and isinstance(value, str):
                out[key] = value.upper()
            else:
                out[key] = _drop_and_uppercase(value)
        return out
    if isinstance(node, list):
        return [_drop_and_uppercase(item) for item in node]
    return node


def _clean_schema(schema: dict[str, Any]) -> dict[str, Any]:
    return _drop_and_uppercase(_inline_refs(schema, schema.get("$defs", {})))


def _name_by_id(messages: list[Message]) -> dict[str, str]:
    return {use.id: use.name for m in messages for use in m.tool_uses}


def _to_gemini_content(message: Message, names: dict[str, str]) -> types.Content:
    parts: list[types.Part] = []
    if message.text:
        parts.append(types.Part(text=message.text))
    for use in message.tool_uses:
        parts.append(
            types.Part(
                function_call=types.FunctionCall(name=use.name, args=use.args),
                thought_signature=use.signature,
            )
        )
    for result in message.tool_results:
        parts.append(
            types.Part(
                function_response=types.FunctionResponse(
                    name=names.get(result.id, result.id),
                    response={"result": result.content},
                )
            )
        )
    return types.Content(role=_ROLE.get(message.role, message.role), parts=parts)


class GeminiProvider:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required with LLM_PROVIDER=gemini")
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    def converse(
        self, system: str, messages: list[Message], tools: list[ToolSpec]
    ) -> Turn:
        names = _name_by_id(messages)
        config = types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=settings.max_tokens,
            tools=[
                types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration(
                            name=tool.name,
                            description=tool.description,
                            parameters=_clean_schema(tool.input_schema),
                        )
                        for tool in tools
                    ]
                )
            ]
            if tools
            else None,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=[_to_gemini_content(m, names) for m in messages],
            config=config,
        )
        candidates = response.candidates or []
        if not candidates:
            return Turn()
        candidate = candidates[0]
        turn = Turn(truncated=candidate.finish_reason == types.FinishReason.MAX_TOKENS)
        parts = candidate.content.parts if candidate.content else None
        for part in parts or []:
            if part.text:
                turn.text += part.text
            elif part.function_call:
                call = part.function_call
                turn.tool_uses.append(
                    ToolUse(
                        id=f"{call.name}:{len(turn.tool_uses)}",
                        name=call.name,
                        args=dict(call.args or {}),
                        signature=part.thought_signature,
                    )
                )
        return turn

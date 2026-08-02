import logging

from pydantic import BaseModel, ValidationError

from hindsight.llm.base import Message, ToolResult, ToolSpec
from hindsight.llm.registry import get_llm

log = logging.getLogger(__name__)

MAX_ATTEMPTS = 3

RETRY_PROMPT = (
    "The arguments you passed to {tool} were invalid: {error}. "
    "Call {tool} again with corrected arguments."
)

CALL_REQUEST = "You did not call {tool}. Call {tool} now with your answer."


def submit_spec(model_cls: type[BaseModel], name: str, description: str) -> ToolSpec:
    return ToolSpec(name=name, description=description, input_schema=model_cls.model_json_schema())


def complete_structured[T: BaseModel](system: str, prompt: str, model_cls: type[T]) -> T:
    tool = submit_spec(model_cls, "submit_result", "Submit your final structured answer.")
    llm = get_llm()
    messages = [Message(role="user", text=prompt)]
    for _ in range(MAX_ATTEMPTS):
        turn = llm.converse(system, messages, [tool])
        use = next((u for u in turn.tool_uses if u.name == tool.name), None)
        if use is None:
            messages.append(Message(role="assistant", text=turn.text or "(no content)"))
            messages.append(Message(role="user", text=CALL_REQUEST.format(tool=tool.name)))
            continue
        try:
            return model_cls.model_validate(use.args)
        except ValidationError as exc:
            log.warning("Invalid structured output: %s", exc)
            messages.append(Message(role="assistant", text=turn.text or None, tool_uses=[use]))
            messages.append(
                Message(
                    role="user",
                    tool_results=[
                        ToolResult(
                            id=use.id,
                            content=RETRY_PROMPT.format(tool=tool.name, error=exc),
                            is_error=True,
                        )
                    ],
                )
            )
    raise RuntimeError(f"LLM failed to produce valid {model_cls.__name__} after {MAX_ATTEMPTS} attempts")

import pytest
from pydantic import BaseModel

from hindsight.llm.base import ToolUse, Turn
from hindsight.llm.structured import complete_structured


class Answer(BaseModel):
    value: int


def _submit(args):
    return Turn(tool_uses=[ToolUse(id="1", name="submit_result", args=args)])


def test_returns_validated_model(fake_llm):
    fake_llm([_submit({"value": 7})])
    assert complete_structured("s", "p", Answer).value == 7


def test_retries_on_invalid_args(fake_llm):
    fake_llm([_submit({"value": "not-an-int-x"}), _submit({"value": 3})])
    assert complete_structured("s", "p", Answer).value == 3


def test_reprompts_when_no_tool_call(fake_llm):
    fake_llm([Turn(text="thinking out loud"), _submit({"value": 1})])
    assert complete_structured("s", "p", Answer).value == 1


def test_raises_after_max_attempts(fake_llm):
    fake_llm([Turn(text="nope")] * 3)
    with pytest.raises(RuntimeError):
        complete_structured("s", "p", Answer)

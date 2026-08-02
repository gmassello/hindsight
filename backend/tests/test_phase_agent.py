import pytest
from pydantic import BaseModel

from hindsight.agent.phase_agent import PhaseFailed, run_phase_agent
from hindsight.llm.base import ToolUse, Turn
from tests.conftest import FakeDataHub


class Outcome(BaseModel):
    answer: str


async def _drain(gen):
    events, result = [], None
    async for kind, item in gen:
        if kind == "event":
            events.append(item)
        else:
            result = item
    return events, result


def _agent(datahub):
    return run_phase_agent(
        phase="test",
        system="s",
        prompt="p",
        datahub=datahub,
        tool_names=["search"],
        result_cls=Outcome,
        submit_name="submit",
        submit_description="d",
    )


@pytest.mark.asyncio
async def test_tool_call_then_submit(fake_llm):
    datahub = FakeDataHub(["search"], {"search": {"hits": 1}})
    fake_llm(
        [
            Turn(tool_uses=[ToolUse(id="1", name="search", args={"query": "x"})]),
            Turn(tool_uses=[ToolUse(id="2", name="submit", args={"answer": "ok"})]),
        ]
    )
    events, result = await _drain(_agent(datahub))
    assert result.answer == "ok"
    assert [e.kind for e in events] == ["tool_call"]
    assert datahub.calls == [("search", {"query": "x"})]


@pytest.mark.asyncio
async def test_premature_submit_is_discarded(fake_llm):
    datahub = FakeDataHub(["search"], {"search": {}})
    fake_llm(
        [
            Turn(
                tool_uses=[
                    ToolUse(id="1", name="search", args={}),
                    ToolUse(id="2", name="submit", args={"answer": "early"}),
                ]
            ),
            Turn(tool_uses=[ToolUse(id="3", name="submit", args={"answer": "final"})]),
        ]
    )
    _, result = await _drain(_agent(datahub))
    assert result.answer == "final"


@pytest.mark.asyncio
async def test_tool_error_is_reported_not_fatal(fake_llm):
    datahub = FakeDataHub(["search"], {"search": RuntimeError("boom")})
    fake_llm(
        [
            Turn(tool_uses=[ToolUse(id="1", name="search", args={})]),
            Turn(tool_uses=[ToolUse(id="2", name="submit", args={"answer": "ok"})]),
        ]
    )
    events, result = await _drain(_agent(datahub))
    assert result.answer == "ok"
    assert events[0].data["error"] is True


@pytest.mark.asyncio
async def test_fails_after_max_turns(fake_llm, monkeypatch):
    monkeypatch.setattr("hindsight.agent.phase_agent.settings.phase_max_turns", 2)
    datahub = FakeDataHub(["search"], {"search": {}})
    fake_llm([Turn(tool_uses=[ToolUse(id=str(i), name="search", args={})]) for i in range(2)])
    with pytest.raises(PhaseFailed):
        await _drain(_agent(datahub))


@pytest.mark.asyncio
async def test_missing_tools_warns_and_falls_back(fake_llm):
    datahub = FakeDataHub(["other_tool"])
    fake_llm([Turn(tool_uses=[ToolUse(id="1", name="submit", args={"answer": "ok"})])])
    events, result = await _drain(_agent(datahub))
    assert result.answer == "ok"
    assert any(e.kind == "warning" for e in events)

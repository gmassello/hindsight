import pytest

from hindsight.agent import orchestrator
from hindsight.agent.context import Ctx
from hindsight.models import InvestigationState, TimelineEvent
from tests.conftest import FakeDataHub


def _ctx() -> Ctx:
    return Ctx(state=InvestigationState(id="t", input_text="x"), datahub=FakeDataHub([]))


async def _ok(ctx):
    yield TimelineEvent(phase="ok", kind="result", message="done")


async def _boom(ctx):
    raise RuntimeError("boom")
    yield


async def _collect(gen):
    return [e async for e in gen]


@pytest.mark.asyncio
async def test_critical_phase_failure_aborts(monkeypatch):
    monkeypatch.setattr(
        orchestrator,
        "INVESTIGATE_PHASES",
        [("intake", "d", _boom, True), ("resolve", "d", _ok, True)],
    )
    ctx = _ctx()
    events = await _collect(orchestrator.investigate(ctx))
    assert ctx.state.status == "failed"
    assert not any(e.phase == "resolve" and e.kind == "result" for e in events)


@pytest.mark.asyncio
async def test_non_critical_failure_continues(monkeypatch):
    monkeypatch.setattr(
        orchestrator,
        "INVESTIGATE_PHASES",
        [("recall", "d", _boom, False), ("impact", "d", _ok, False)],
    )
    ctx = _ctx()
    events = await _collect(orchestrator.investigate(ctx))
    assert ctx.state.status == "awaiting_approval"
    assert any(e.phase == "impact" and e.kind == "start" for e in events)
    assert any(e.kind == "error" for e in events)

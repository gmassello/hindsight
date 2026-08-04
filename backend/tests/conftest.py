from typing import Any

import pytest

from hindsight.llm.base import ToolSpec, Turn
from hindsight.models import (
    BlastRadius,
    EntityRef,
    Hypothesis,
    ImpactedAsset,
    Incident,
    InvestigationState,
    ResolveResult,
)


def make_state(**overrides: Any) -> InvestigationState:
    fields: dict[str, Any] = {
        "id": "abc",
        "input_text": "nulls in fct_orders",
        "incident": Incident(
            symptom_type="nulls",
            symptom_description="customer_id is null",
            detected_at="2026-08-08 03:00 UTC",
        ),
        "resolution": ResolveResult(
            resolved_asset=EntityRef(urn="urn:li:dataset:(dbt,fct_orders,PROD)", name="fct_orders")
        ),
        "blast_radius": BlastRadius(
            impacted=[
                ImpactedAsset(
                    urn="urn:li:dashboard:x", name="exec_revenue", type="dashboard",
                    hops=2, score=4.5, owners=["urn:li:corpuser:ana"],
                )
            ],
            total_score=4.5,
            owners_to_notify=["urn:li:corpuser:ana"],
        ),
        "hypotheses": [
            Hypothesis(
                cause_type="schema_drift_upstream",
                statement="raw_customers dropped customer_id",
                confidence=0.8,
                evidence=["column missing in schema"],
                evidence_urns=["urn:li:dataset:(dbt,raw_customers,PROD)"],
            )
        ],
    }
    fields.update(overrides)
    return InvestigationState(**fields)


class FakeDataHub:
    def __init__(self, tools: list[str], responses: dict[str, Any] | None = None):
        self.tools = {
            name: ToolSpec(name=name, description=name, input_schema={"type": "object"})
            for name in tools
        }
        self.responses = responses or {}
        self.calls: list[tuple[str, dict]] = []

    def has(self, name: str) -> bool:
        return name in self.tools

    def specs(self, names: list[str]) -> list[ToolSpec]:
        return [self.tools[n] for n in names if n in self.tools]

    def read_tools(self) -> list[ToolSpec]:
        return list(self.tools.values())

    async def call(self, name: str, args: dict) -> Any:
        self.calls.append((name, args))
        response = self.responses.get(name, {})
        if isinstance(response, Exception):
            raise response
        return response


class FakeLLM:
    def __init__(self, turns: list[Turn]):
        self.turns = list(turns)
        self.requests: list[tuple[str, list, list]] = []

    def converse(self, system, messages, tools) -> Turn:
        self.requests.append((system, list(messages), list(tools)))
        return self.turns.pop(0)


@pytest.fixture
def fake_llm(monkeypatch):
    def install(turns: list[Turn]) -> FakeLLM:
        llm = FakeLLM(turns)
        monkeypatch.setattr("hindsight.llm.structured.get_llm", lambda: llm)
        monkeypatch.setattr("hindsight.agent.phase_agent.get_llm", lambda: llm)
        return llm

    return install

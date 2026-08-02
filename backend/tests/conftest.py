from typing import Any

import pytest

from hindsight.llm.base import ToolSpec, Turn


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

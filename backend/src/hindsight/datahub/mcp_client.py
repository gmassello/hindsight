import json
import os
import shlex
from contextlib import AsyncExitStack
from typing import Any, Self

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

from hindsight.config import settings
from hindsight.llm.base import ToolSpec, as_text

MUTATION_PREFIXES = ("add_", "update_", "set_", "remove_", "save_", "create_", "delete_")


class DataHubMCPError(RuntimeError):
    pass


class DataHubMCP:
    def __init__(self) -> None:
        self.url = settings.datahub_mcp_url
        self.token = settings.datahub_gms_token
        self.session: ClientSession | None = None
        self.tools: dict[str, ToolSpec] = {}
        self._read_only: dict[str, bool] = {}
        self._stack = AsyncExitStack()

    async def _transport(self):
        if self.url:
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            read, write, _ = await self._stack.enter_async_context(
                streamablehttp_client(self.url, headers=headers)
            )
            return read, write
        command, *args = shlex.split(settings.datahub_mcp_command)
        params = StdioServerParameters(
            command=command,
            args=args,
            env={
                **os.environ,
                "DATAHUB_GMS_URL": settings.datahub_gms_url,
                "DATAHUB_GMS_TOKEN": self.token,
                "TOOLS_IS_MUTATION_ENABLED": "true",
                "TOOLS_IS_USER_ENABLED": "true",
            },
        )
        errlog = self._stack.enter_context(open(os.devnull, "w"))  # noqa: ASYNC230, SIM115
        read, write = await self._stack.enter_async_context(stdio_client(params, errlog=errlog))
        return read, write

    async def __aenter__(self) -> Self:
        read, write = await self._transport()
        self.session = await self._stack.enter_async_context(ClientSession(read, write))
        await self.session.initialize()
        listing = await self.session.list_tools()
        for tool in listing.tools:
            self.tools[tool.name] = ToolSpec(
                name=tool.name,
                description=tool.description or "",
                input_schema=tool.inputSchema or {"type": "object", "properties": {}},
            )
            hint = tool.annotations.readOnlyHint if tool.annotations else None
            self._read_only[tool.name] = (
                hint if hint is not None else not tool.name.startswith(MUTATION_PREFIXES)
            )
        return self

    async def __aexit__(self, *exc) -> None:
        await self._stack.aclose()

    def has(self, name: str) -> bool:
        return name in self.tools

    def read_tools(self) -> list[ToolSpec]:
        return [spec for name, spec in self.tools.items() if self._read_only.get(name)]

    def specs(self, names: list[str]) -> list[ToolSpec]:
        return [self.tools[n] for n in names if n in self.tools]

    async def call(self, name: str, args: dict[str, Any]) -> Any:
        if self.session is None:
            raise DataHubMCPError("MCP session not open")
        if name not in self.tools:
            raise DataHubMCPError(f"Tool {name} is not exposed by the DataHub MCP server")
        result = await self.session.call_tool(name, args)
        payload = _parse_content(result.content)
        if result.isError:
            raise DataHubMCPError(f"{name} failed: {as_text(payload)[:500]}")
        return payload


def _parse_content(content: list[Any]) -> Any:
    texts = [block.text for block in content if getattr(block, "text", None)]
    joined = "\n".join(texts)
    try:
        return json.loads(joined)
    except (json.JSONDecodeError, TypeError):
        return joined

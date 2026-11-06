"""Reusable local MCP client for enterprise agents."""

import json
import os
import sys

from mcp import Client, StdioServerParameters


class EnterpriseMCPClient:
    """Local MCP transport, discovery and invocation."""

    def __init__(self, role: str = "reader"):
        self.role = role
        self.client = None

    async def __aenter__(self):
        server = StdioServerParameters(
            command=sys.executable,
            args=["-m", "src.server.main"],
            env={
                **os.environ,
                "AI_A04_ROLE": self.role,
            },
        )

        self.client = Client(server)
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return await self.client.__aexit__(
            exc_type, exc, tb
        )

    async def discover_tools(self) -> list[str]:
        """Discover available MCP tool names."""
        result = await self.client.list_tools()
        return [tool.name for tool in result.tools]

    async def call(
        self,
        tool_name: str,
        arguments: dict,
    ) -> dict:
        """Invoke an MCP tool and decode its result."""

        result = await self.client.call_tool(
            tool_name,
            arguments,
        )

        if result.is_error:
            raise RuntimeError(
                f"MCP tool {tool_name} failed: "
                f"{result.content}"
            )

        if result.structured_content is not None:
            return result.structured_content

        for block in result.content:
            if block.type == "text":
                data = json.loads(block.text)
                if not isinstance(data, dict):
                    raise ValueError(
                        "Expected JSON object from MCP tool"
                    )
                return data

        raise RuntimeError(
            f"No JSON response from MCP tool {tool_name}"
        )

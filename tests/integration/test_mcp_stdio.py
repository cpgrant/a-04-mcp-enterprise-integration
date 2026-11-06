import os
"""Integration test for independent MCP client/server processes."""

import asyncio
import json
import sys

from mcp import Client, StdioServerParameters


async def run_test():
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "src.server.main"],
        env={
            **os.environ,
            "AI_A04_ROLE": "reader",
        },
    )

    async with Client(server) as client:
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools.tools]

        assert "get_customer" in tool_names
        assert "list_customers" in tool_names

        result = await client.call_tool(
            "get_customer",
            {"customer_id": "C001"},
        )

        assert not result.is_error

        if result.structured_content is not None:
            customer = result.structured_content
        else:
            customer = json.loads(
                next(
                    block.text
                    for block in result.content
                    if block.type == "text"
                )
            )

        assert customer["id"] == "C001"

        resources = await client.list_resources()

        resource_uris = [
            str(resource.uri)
            for resource in resources.resources
        ]

        assert "enterprise://catalog" in resource_uris


def test_mcp_stdio():
    asyncio.run(run_test())

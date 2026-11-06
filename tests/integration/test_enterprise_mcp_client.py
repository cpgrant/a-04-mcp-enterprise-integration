"""Tests for the reusable enterprise MCP client."""

import asyncio

from src.client.enterprise_mcp import EnterpriseMCPClient


async def check_client():
    async with EnterpriseMCPClient() as mcp:
        tools = await mcp.discover_tools()

        assert len(tools) == 9
        assert "get_customer_db" in tools

        customer = await mcp.call(
            "get_customer_db",
            {"customer_code": "C001"},
        )

        assert customer["found"] is True
        assert customer["customer"]["customer_code"] == "C001"


def test_reusable_mcp_client():
    asyncio.run(check_client())

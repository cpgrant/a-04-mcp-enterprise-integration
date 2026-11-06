import os
"""End-to-end tests of database-backed MCP tools."""

import asyncio
import json
import sys

from mcp import Client, StdioServerParameters


def unpack(result):
    assert not result.is_error

    if result.structured_content is not None:
        return result.structured_content

    return json.loads(
        next(
            block.text
            for block in result.content
            if block.type == "text"
        )
    )


async def check_database_tools():
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "src.server.main"],
        env={
            **os.environ,
            "AI_A04_ROLE": "reader",
        },
    )

    async with Client(server) as client:

        result = unpack(
            await client.call_tool(
                "get_customer_db",
                {"customer_code": "C001"},
            )
        )

        assert result["found"] is True
        assert result["customer"]["customer_name"] == "ACME Corporation"
        assert result["source"] == "postgresql.crm.customers"

        listing = unpack(
            await client.call_tool(
                "list_customers_db",
                {"limit": 3},
            )
        )

        assert listing["count"] == 3

        missing = unpack(
            await client.call_tool(
                "get_customer_db",
                {"customer_code": "NOT-FOUND"},
            )
        )

        assert missing["found"] is False


def test_postgresql_backed_mcp():
    asyncio.run(check_database_tools())

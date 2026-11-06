import os
"""Cross-domain MCP integration tests."""

import asyncio
import json
import sys

from mcp import Client, StdioServerParameters


def decode(result):
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


async def verify_enterprise():
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
        names = {tool.name for tool in tools.tools}

        required = {
            "get_customer_orders_db",
            "get_order_details_db",
            "get_inventory_status_db",
            "list_customer_invoices_db",
            "get_customer_financial_summary_db",
        }

        assert required.issubset(names)

        async def call(name, arguments):
            return decode(await client.call_tool(name, arguments))

        orders = await call(
            "get_customer_orders_db",
            {"customer_code": "C001", "limit": 20},
        )
        assert orders["count"] == 4

        order = await call(
            "get_order_details_db",
            {"order_number": "SO-0001"},
        )
        assert order["order"]["order_total"] == "1085.00"

        inventory = await call(
            "get_inventory_status_db",
            {"sku": "SKU-006"},
        )
        assert inventory["inventory"]["quantity_available"] == 2

        invoices = await call(
            "list_customer_invoices_db",
            {"customer_code": "C001", "as_of": "2026-11-06"},
        )
        assert invoices["count"] == 4

        finance = await call(
            "get_customer_financial_summary_db",
            {"customer_code": "C001", "as_of": "2026-11-06"},
        )
        assert finance["total_outstanding"] == "7612.50"
        assert finance["overdue_balance"] == "6527.50"


def test_cross_domain_enterprise_mcp():
    asyncio.run(verify_enterprise())

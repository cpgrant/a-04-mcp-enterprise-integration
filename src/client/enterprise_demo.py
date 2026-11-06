"""AI-A04: Cross-domain enterprise MCP demonstration."""

import asyncio
import os
import json
import sys

from mcp import Client, StdioServerParameters


def unpack(result):
    if result.is_error:
        raise RuntimeError(f"MCP tool error: {result.content}")

    if result.structured_content is not None:
        return result.structured_content

    for block in result.content:
        if block.type == "text":
            return json.loads(block.text)

    raise RuntimeError("MCP response contains no JSON data")


async def main():
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
        names = [tool.name for tool in tools.tools]

        print("=== MCP Enterprise Tool Catalogue ===")
        for name in names:
            print(" -", name)

        assert len(names) == 9, f"Expected 9 tools, got {len(names)}"

        async def call(name, arguments):
            result = await client.call_tool(name, arguments)
            return unpack(result)

        customer = await call(
            "get_customer_db",
            {"customer_code": "C001"},
        )

        orders = await call(
            "get_customer_orders_db",
            {"customer_code": "C001", "limit": 20},
        )

        invoices = await call(
            "list_customer_invoices_db",
            {
                "customer_code": "C001",
                "as_of": "2026-11-06",
            },
        )

        finance = await call(
            "get_customer_financial_summary_db",
            {
                "customer_code": "C001",
                "as_of": "2026-11-06",
            },
        )

        inventory = await call(
            "get_inventory_status_db",
            {"sku": "SKU-006"},
        )

        order_details = await call(
            "get_order_details_db",
            {"order_number": "SO-0001"},
        )

        assert customer["found"]
        assert orders["count"] == 4
        assert invoices["count"] == 4
        assert finance["total_outstanding"] == "7612.50"
        assert finance["overdue_balance"] == "6527.50"
        assert inventory["inventory"]["quantity_available"] == 2
        assert order_details["order"]["order_total"] == "1085.00"

        report = {
            "customer": customer["customer"],
            "orders": orders["orders"],
            "financial_summary": finance,
            "invoice_count": invoices["count"],
            "sample_inventory": inventory["inventory"],
            "sample_order": order_details["order"],
        }

        print("\\n=== Enterprise Business Assessment ===")
        print(json.dumps(report, indent=2))

    print("\\nPASS: Cross-domain Enterprise MCP integration")


if __name__ == "__main__":
    asyncio.run(main())

"""AI-A04: PostgreSQL-backed MCP demonstration."""

import asyncio
import json
import sys

from mcp import Client, StdioServerParameters


def unpack_result(result):
    """Extract JSON data from an MCP tool response."""

    if result.is_error:
        raise RuntimeError(f"MCP tool failed: {result.content}")

    if result.structured_content is not None:
        return result.structured_content

    for block in result.content:
        if block.type == "text":
            return json.loads(block.text)

    raise RuntimeError("No JSON content returned")


async def main():
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "src.server.main"],
    )

    async with Client(server) as client:

        tools = await client.list_tools()
        names = [tool.name for tool in tools.tools]

        print("=== Available MCP Tools ===")
        for name in names:
            print(" -", name)

        assert "get_customer_db" in names
        assert "list_customers_db" in names

        print("\\n=== PostgreSQL Customer Lookup ===")

        result = await client.call_tool(
            "get_customer_db",
            {"customer_code": "C001"},
        )

        customer_result = unpack_result(result)

        print(json.dumps(customer_result, indent=2))

        assert customer_result["found"] is True
        assert customer_result["customer"]["customer_code"] == "C001"
        assert customer_result["customer"]["country"] == "DE"

        print("\\n=== Customer Listing ===")

        result = await client.call_tool(
            "list_customers_db",
            {"limit": 5},
        )

        customers_result = unpack_result(result)

        print("Count:", customers_result["count"])

        assert customers_result["count"] == 5

        print("\\n=== Missing Customer ===")

        result = await client.call_tool(
            "get_customer_db",
            {"customer_code": "UNKNOWN"},
        )

        missing = unpack_result(result)

        assert missing["found"] is False

        print("Missing customer handled correctly")

    print("\\nPASS: PostgreSQL-backed MCP integration")


if __name__ == "__main__":
    asyncio.run(main())

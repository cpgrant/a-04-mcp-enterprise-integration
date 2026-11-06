"""AI-A04: MCP client over stdio."""

import asyncio
import json
import sys

from mcp import Client, StdioServerParameters


async def main():
    server_command = StdioServerParameters(
        command=sys.executable,
        args=["-m", "src.server.main"],
    )

    async with Client(server_command) as client:

        tools = await client.list_tools()

        print("\nDiscovered MCP tools:")
        tool_names = [tool.name for tool in tools.tools]

        for name in tool_names:
            print(f"  - {name}")

        assert "get_customer" in tool_names

        result = await client.call_tool(
            "get_customer",
            {"customer_id": "C001"},
        )

        assert not result.is_error, "MCP tool failed"

        # SDK v2 can return data in content blocks.
        if result.structured_content is not None:
            customer = result.structured_content
        else:
            text_blocks = [
                block.text
                for block in result.content
                if block.type == "text"
            ]

            assert text_blocks, "No MCP text content"
            customer = json.loads(text_blocks[0])

        assert customer["id"] == "C001"
        assert customer["name"] == "ACME Corporation"

        print("\nCustomer:")
        print(json.dumps(customer, indent=2))

        resources = await client.list_resources()

        print("\nResources:")
        for resource in resources.resources:
            print(f"  - {resource.uri}")

        print("\nPASS: Independent MCP client/server communication")


if __name__ == "__main__":
    asyncio.run(main())

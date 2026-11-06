"""AI-A04: First MCP client demonstration."""

import asyncio
from pprint import pprint

from mcp import Client
from src.server.main import mcp


async def main():
    async with Client(mcp, raise_exceptions=True) as client:

        # Discover tools
        tools_result = await client.list_tools()

        print("\nAvailable MCP tools:")
        for tool in tools_result.tools:
            print(f"  - {tool.name}")

        # Invoke customer tool
        result = await client.call_tool(
            "get_customer",
            {"customer_id": "C001"},
        )

        print("\nCustomer result:")
        print("is_error:", result.is_error)
        print("structured_content:")
        pprint(result.structured_content)
        print("content blocks:")
        for block in result.content:
            pprint(block.model_dump(exclude_none=True))

        if result.is_error:
            raise RuntimeError("MCP tool returned an error")

        # Discover resources
        resources_result = await client.list_resources()

        print("\nAvailable MCP resources:")
        for resource in resources_result.resources:
            print(f"  - {resource.uri}")

    print("\nAI-A04 MCP CLIENT TEST PASSED")


if __name__ == "__main__":
    asyncio.run(main())

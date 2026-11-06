"""AI-A04: Enterprise MCP server, Day 1."""

from mcp.server import MCPServer

mcp = MCPServer("AI-A04 Enterprise Integration")

CUSTOMERS = {
    "C001": {
        "id": "C001",
        "name": "ACME Corporation",
        "status": "active",
    },
    "C002": {
        "id": "C002",
        "name": "Northwind Trading",
        "status": "active",
    },
}


@mcp.tool()
def get_customer(customer_id: str) -> dict:
    """Retrieve a customer by ID."""
    customer = CUSTOMERS.get(customer_id)
    if customer is None:
        return {"error": "Customer not found"}
    return customer


@mcp.tool()
def list_customers() -> list[dict]:
    """List customers in the synthetic enterprise dataset."""
    return list(CUSTOMERS.values())


@mcp.resource("enterprise://catalog")
def enterprise_catalog() -> str:
    """Describe the available enterprise data."""
    return "AI-A04 synthetic enterprise customer catalogue"


if __name__ == "__main__":
    mcp.run(transport="stdio")

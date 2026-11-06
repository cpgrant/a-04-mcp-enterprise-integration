"""AI-A04: Enterprise MCP server, Day 1."""

from src.governance.policy import require_tool


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
@require_tool("get_customer")
def get_customer(customer_id: str) -> dict:
    """Retrieve a customer by ID."""
    customer = CUSTOMERS.get(customer_id)
    if customer is None:
        return {"error": "Customer not found"}
    return customer


@mcp.tool()
@require_tool("list_customers")
def list_customers() -> list[dict]:
    """List customers in the synthetic enterprise dataset."""
    return list(CUSTOMERS.values())


@mcp.resource("enterprise://catalog")
def enterprise_catalog() -> str:
    """Describe the available enterprise data."""
    return "AI-A04 synthetic enterprise customer catalogue"



# ===========================================
# Day 2: PostgreSQL-backed enterprise tools
# ===========================================

from src.adapters.crm.customers import (
    get_customer as crm_get_customer,
    list_customers as crm_list_customers,
)


@mcp.tool()
@require_tool("get_customer_db")
def get_customer_db(customer_code: str) -> dict:
    """Retrieve customer master data from PostgreSQL."""

    customer = crm_get_customer(customer_code)

    if customer is None:
        return {
            "found": False,
            "customer_code": customer_code,
            "message": "Customer not found",
        }

    return {
        "found": True,
        "customer": customer,
        "source": "postgresql.crm.customers",
    }


@mcp.tool()
@require_tool("list_customers_db")
def list_customers_db(limit: int = 25) -> dict:
    """List customers from PostgreSQL."""

    customers = crm_list_customers(limit)

    return {
        "count": len(customers),
        "customers": customers,
        "source": "postgresql.crm.customers",
    }



# ====================================================
# Day 2: Enterprise ERP and Finance MCP tools
# ====================================================

from datetime import date

from src.adapters.erp.orders import (
    get_customer_orders as erp_customer_orders,
    get_order_details as erp_order_details,
    get_inventory_status as erp_inventory_status,
)

from src.adapters.finance.invoices import (
    list_customer_invoices as finance_customer_invoices,
    get_customer_financial_summary as finance_summary,
)


@mcp.tool()
@require_tool("get_customer_orders_db")
def get_customer_orders_db(
    customer_code: str,
    limit: int = 20,
) -> dict:
    """Retrieve recent customer orders from ERP."""

    orders = erp_customer_orders(customer_code, limit)

    return {
        "customer_code": customer_code,
        "count": len(orders),
        "orders": orders,
        "source": "postgresql.erp.sales_orders",
    }


@mcp.tool()
@require_tool("get_order_details_db")
def get_order_details_db(order_number: str) -> dict:
    """Retrieve a sales order and its product lines."""

    order = erp_order_details(order_number)

    return {
        "found": order is not None,
        "order": order,
        "source": "postgresql.erp.sales_orders",
    }


@mcp.tool()
@require_tool("get_inventory_status_db")
def get_inventory_status_db(sku: str) -> dict:
    """Retrieve product inventory and availability."""

    inventory = erp_inventory_status(sku)

    return {
        "found": inventory is not None,
        "inventory": inventory,
        "source": "postgresql.erp.inventory",
    }


@mcp.tool()
@require_tool("list_customer_invoices_db")
def list_customer_invoices_db(
    customer_code: str,
    as_of: str,
) -> dict:
    """Retrieve customer invoices as of a specified ISO date."""

    reference_date = date.fromisoformat(as_of)

    invoices = finance_customer_invoices(
        customer_code,
        as_of=reference_date,
    )

    return {
        "customer_code": customer_code,
        "as_of": as_of,
        "count": len(invoices),
        "invoices": invoices,
        "source": "postgresql.finance.invoices",
    }


@mcp.tool()
@require_tool("get_customer_financial_summary_db")
def get_customer_financial_summary_db(
    customer_code: str,
    as_of: str,
) -> dict:
    """Calculate invoiced, paid, outstanding and overdue totals."""

    reference_date = date.fromisoformat(as_of)

    result = finance_summary(
        customer_code,
        as_of=reference_date,
    )

    return {
        **result,
        "source": "postgresql.finance",
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")

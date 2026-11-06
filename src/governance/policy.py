"""Local demonstration policy for AI-A04."""

import os
from functools import wraps


FINANCE_TOOLS = {
    "list_customer_invoices_db",
    "get_customer_financial_summary_db",
}

CUSTOMER_TOOLS = {
    "get_customer",
    "list_customers",
    "get_customer_db",
    "list_customers_db",
}

ERP_TOOLS = {
    "get_customer_orders_db",
    "get_order_details_db",
    "get_inventory_status_db",
}

ALL_TOOLS = CUSTOMER_TOOLS | ERP_TOOLS | FINANCE_TOOLS

ROLE_PERMISSIONS = {
    "reader": ALL_TOOLS,
    "finance_reader": CUSTOMER_TOOLS | FINANCE_TOOLS,
    "blocked": set(),
}


def is_allowed(role: str, tool_name: str) -> bool:
    """Check whether the role may execute a tool."""
    return tool_name in ROLE_PERMISSIONS.get(role, set())


def require_tool(tool_name: str):
    """Enforce the local launcher's role before executing a tool."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            role = os.getenv("AI_A04_ROLE", "blocked")

            from src.governance.audit import record_event

            if not is_allowed(role, tool_name):
                record_event(tool_name, role, "denied")
                raise PermissionError(
                    f"Tool access denied: {tool_name}"
                )

            try:
                result = func(*args, **kwargs)
            except Exception:
                record_event(tool_name, role, "error")
                raise

            record_event(tool_name, role, "success")
            return result

        return wrapper

    return decorator

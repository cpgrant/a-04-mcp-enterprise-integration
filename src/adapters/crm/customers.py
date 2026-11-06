"""CRM data access adapter."""

from src.adapters.db import get_connection


def get_customer(customer_code: str) -> dict | None:
    """Retrieve customer master data from PostgreSQL."""

    query = """
        SELECT
            customer_code,
            customer_name,
            industry,
            country,
            status
        FROM crm.customers
        WHERE customer_code = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (customer_code,))
            return cur.fetchone()


def list_customers(limit: int = 25) -> list[dict]:
    """Return a limited list of enterprise customers."""

    if isinstance(limit, bool) or not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")

    query = """
        SELECT
            customer_code,
            customer_name,
            industry,
            country,
            status
        FROM crm.customers
        ORDER BY customer_code
        LIMIT %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (limit,))
            return cur.fetchall()

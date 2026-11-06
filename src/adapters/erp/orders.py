"""ERP order and inventory access for AI-A04."""

from decimal import Decimal

from src.adapters.db import get_connection


def get_customer_orders(
    customer_code: str,
    limit: int = 20,
) -> list[dict]:
    """Retrieve a customer's recent sales orders."""

    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")

    query = """
        SELECT
            o.order_number,
            c.customer_code,
            o.order_date,
            o.status,
            o.currency,
            COALESCE(SUM(ol.line_total), 0) AS order_total
        FROM erp.sales_orders o
        JOIN crm.customers c
            ON c.customer_id = o.customer_id
        LEFT JOIN erp.order_lines ol
            ON ol.order_id = o.order_id
        WHERE c.customer_code = %s
        GROUP BY
            o.order_id,
            o.order_number,
            c.customer_code,
            o.order_date,
            o.status,
            o.currency
        ORDER BY o.order_date DESC, o.order_number DESC
        LIMIT %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (customer_code, limit))
            rows = cur.fetchall()

    for row in rows:
        row["order_date"] = row["order_date"].isoformat()
        row["order_total"] = str(row["order_total"])

    return rows


def get_order_details(order_number: str) -> dict | None:
    """Retrieve order header and associated product lines."""

    header_query = """
        SELECT
            o.order_number,
            c.customer_code,
            c.customer_name,
            o.order_date,
            o.status,
            o.currency
        FROM erp.sales_orders o
        JOIN crm.customers c
            ON c.customer_id = o.customer_id
        WHERE o.order_number = %s
    """

    lines_query = """
        SELECT
            p.sku,
            p.product_name,
            ol.quantity,
            ol.unit_price,
            ol.line_total
        FROM erp.order_lines ol
        JOIN erp.sales_orders o
            ON o.order_id = ol.order_id
        JOIN erp.products p
            ON p.product_id = ol.product_id
        WHERE o.order_number = %s
        ORDER BY p.sku
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(header_query, (order_number,))
            order = cur.fetchone()

            if order is None:
                return None

            cur.execute(lines_query, (order_number,))
            lines = cur.fetchall()

    order["order_date"] = order["order_date"].isoformat()

    for line in lines:
        line["unit_price"] = str(line["unit_price"])
        line["line_total"] = str(line["line_total"])

    order["lines"] = lines
    order["order_total"] = str(
        sum(
            (int(line["quantity"]) *
             Decimal(line["unit_price"])
             for line in lines),
            Decimal("0"),
        )
    )

    return order


def get_inventory_status(sku: str) -> dict | None:
    """Retrieve inventory position for a product."""

    query = """
        SELECT
            p.sku,
            p.product_name,
            i.quantity_on_hand,
            i.quantity_reserved,
            i.quantity_on_hand - i.quantity_reserved
                AS quantity_available,
            i.reorder_level,
            (i.quantity_on_hand - i.quantity_reserved)
                < i.reorder_level AS below_reorder_level
        FROM erp.inventory i
        JOIN erp.products p
            ON p.product_id = i.product_id
        WHERE p.sku = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (sku,))
            return cur.fetchone()

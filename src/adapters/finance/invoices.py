"""Financial data access and reconciliation for AI-A04."""

from datetime import date
from decimal import Decimal

from src.adapters.db import get_connection


INVOICE_BALANCES = """
WITH billed AS (
    SELECT invoice_id, SUM(line_total) AS total
    FROM finance.invoice_lines
    GROUP BY invoice_id
),
paid AS (
    SELECT invoice_id, SUM(amount) AS total
    FROM finance.payments
    GROUP BY invoice_id
)
SELECT
    i.invoice_number,
    c.customer_code,
    i.invoice_date,
    i.due_date,
    i.status,
    i.currency,
    COALESCE(b.total, 0)::numeric(14,2) AS invoice_total,
    COALESCE(p.total, 0)::numeric(14,2) AS paid_total,
    (
        COALESCE(b.total, 0) - COALESCE(p.total, 0)
    )::numeric(14,2) AS outstanding_balance
FROM finance.invoices i
JOIN crm.customers c
    ON c.customer_id = i.customer_id
LEFT JOIN billed b
    ON b.invoice_id = i.invoice_id
LEFT JOIN paid p
    ON p.invoice_id = i.invoice_id
WHERE c.customer_code = %s
"""


def list_customer_invoices(
    customer_code: str,
    as_of: date | None = None,
) -> list[dict]:
    """Return customer invoices with calculated balances."""

    reference_date = as_of or date.today()

    query = (
        INVOICE_BALANCES
        + " ORDER BY i.invoice_date DESC, i.invoice_number DESC"
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (customer_code,))
            rows = cur.fetchall()

    for row in rows:
        row["is_overdue"] = (
            row["due_date"] < reference_date
            and row["outstanding_balance"] > 0
            and row["status"] != "void"
        )

        row["invoice_date"] = row["invoice_date"].isoformat()
        row["due_date"] = row["due_date"].isoformat()

        for field in (
            "invoice_total",
            "paid_total",
            "outstanding_balance",
        ):
            row[field] = str(row[field])

    return rows


def get_customer_financial_summary(
    customer_code: str,
    as_of: date | None = None,
) -> dict:
    """Calculate a customer-level financial summary."""

    reference_date = as_of or date.today()

    invoices = list_customer_invoices(
        customer_code,
        as_of=reference_date,
    )

    def total(field):
        return sum(
            (Decimal(i[field]) for i in invoices),
            Decimal("0.00"),
        )

    overdue_balance = sum(
        (
            Decimal(i["outstanding_balance"])
            for i in invoices
            if i["is_overdue"]
        ),
        Decimal("0.00"),
    )

    return {
        "customer_code": customer_code,
        "as_of": reference_date.isoformat(),
        "currency": "EUR",
        "invoice_count": len(invoices),
        "overdue_invoice_count": sum(
            i["is_overdue"] for i in invoices
        ),
        "total_invoiced": str(total("invoice_total")),
        "total_paid": str(total("paid_total")),
        "total_outstanding": str(total("outstanding_balance")),
        "overdue_balance": str(overdue_balance),
    }

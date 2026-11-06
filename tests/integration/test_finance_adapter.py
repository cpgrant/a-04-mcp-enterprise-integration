"""Tests for enterprise financial reconciliation."""

from datetime import date
from decimal import Decimal

from src.adapters.finance.invoices import (
    list_customer_invoices,
    get_customer_financial_summary,
)


REFERENCE_DATE = date(2026, 11, 6)


def test_customer_invoice_count():
    invoices = list_customer_invoices(
        "C001", as_of=REFERENCE_DATE
    )
    assert len(invoices) == 4


def test_acme_financial_summary():
    result = get_customer_financial_summary(
        "C001", as_of=REFERENCE_DATE
    )

    assert result["invoice_count"] == 4
    assert Decimal(result["total_invoiced"]) == Decimal("11690.00")
    assert Decimal(result["total_paid"]) == Decimal("4077.50")
    assert Decimal(result["total_outstanding"]) == Decimal("7612.50")


def test_overdue_balance():
    result = get_customer_financial_summary(
        "C001", as_of=REFERENCE_DATE
    )

    assert result["overdue_invoice_count"] == 2
    assert Decimal(result["overdue_balance"]) == Decimal("6527.50")


def test_unknown_customer_financial_summary():
    result = get_customer_financial_summary(
        "UNKNOWN", as_of=REFERENCE_DATE
    )

    assert result["invoice_count"] == 0
    assert Decimal(result["total_outstanding"]) == 0


def test_financial_reconciliation():
    result = get_customer_financial_summary(
        "C001", as_of=REFERENCE_DATE
    )

    invoiced = Decimal(result["total_invoiced"])
    paid = Decimal(result["total_paid"])
    outstanding = Decimal(result["total_outstanding"])

    assert invoiced == paid + outstanding

"""Tests for database-backed ERP operations."""

import pytest

from src.adapters.erp.orders import (
    get_customer_orders,
    get_order_details,
    get_inventory_status,
)


def test_customer_orders():
    orders = get_customer_orders("C001")

    assert len(orders) == 4
    assert all(o["customer_code"] == "C001" for o in orders)


def test_order_details():
    order = get_order_details("SO-0001")

    assert order is not None
    assert order["order_total"] == "1085.00"
    assert len(order["lines"]) == 2


def test_missing_order():
    assert get_order_details("UNKNOWN") is None


def test_inventory_shortage():
    item = get_inventory_status("SKU-006")

    assert item is not None
    assert item["quantity_available"] == 2
    assert item["below_reorder_level"] is True


def test_invalid_order_limit():
    with pytest.raises(ValueError):
        get_customer_orders("C001", limit=101)

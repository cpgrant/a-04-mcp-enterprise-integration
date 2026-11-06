"""Unit tests for the initial enterprise customer tools."""

from src.server.main import get_customer, list_customers


def test_get_existing_customer():
    customer = get_customer("C001")

    assert customer["id"] == "C001"
    assert customer["name"] == "ACME Corporation"
    assert customer["status"] == "active"


def test_get_missing_customer():
    result = get_customer("UNKNOWN")

    assert result["error"] == "Customer not found"


def test_list_customers():
    customers = list_customers()

    assert len(customers) == 2
    assert any(c["id"] == "C001" for c in customers)

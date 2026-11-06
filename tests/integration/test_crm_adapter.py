"""CRM PostgreSQL integration tests."""

import pytest

from src.adapters.crm.customers import (
    get_customer,
    list_customers,
)


def test_customer_lookup():
    customer = get_customer("C001")

    assert customer is not None
    assert customer["customer_name"] == "ACME Corporation"
    assert customer["status"] == "active"


def test_missing_customer():
    assert get_customer("UNKNOWN") is None


def test_list_customers():
    customers = list_customers(5)

    assert len(customers) == 5
    assert customers[0]["customer_code"] == "C001"


def test_invalid_list_limit():
    with pytest.raises(ValueError):
        list_customers(101)

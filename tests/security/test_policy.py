"""Local authorization policy tests."""

import pytest

from src.governance.policy import (
    is_allowed,
    require_tool,
)


def test_reader_can_read_erp():
    assert is_allowed("reader", "get_customer_orders_db")


def test_finance_reader_can_access_finance():
    assert is_allowed(
        "finance_reader",
        "get_customer_financial_summary_db"
    )


def test_finance_reader_cannot_access_erp():
    assert not is_allowed(
        "finance_reader",
        "get_customer_orders_db"
    )


def test_blocked_role_denied():
    assert not is_allowed("blocked", "get_customer_db")


def test_unknown_role_denied():
    assert not is_allowed("administrator", "get_customer_db")


def test_denied_tool_is_not_executed(monkeypatch):
    monkeypatch.setenv("AI_A04_ROLE", "blocked")

    executed = []

    @require_tool("get_customer_db")
    def protected():
        executed.append(True)
        return {"ok": True}

    with pytest.raises(PermissionError):
        protected()

    assert executed == []

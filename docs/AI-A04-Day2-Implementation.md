# AI-A04 — Day 2: Enterprise Integration Implementation

## Objective

Extend the Day 1 MCP foundation with database-backed
enterprise capabilities, governance and automated validation.

## Architecture

MCP Client
    -> MCP Server
    -> Local Policy Enforcement
    -> Enterprise Adapters
    -> PostgreSQL

Audit events are emitted to stderr.

## Technology

- Python 3.12
- MCP Python SDK 2.3.0
- PostgreSQL 17
- Psycopg 3
- Pydantic
- pytest
- Docker Compose

## Database

Database: a04_enterprise

Schemas:

- crm: customers, contacts
- erp: products, sales_orders, order_lines, inventory
- finance: invoices, invoice_lines, payments

The database contains 715 reproducible synthetic records
across nine relational tables.

## Enterprise Adapters

### CRM

- get_customer
- list_customers

### ERP

- get_customer_orders
- get_order_details
- get_inventory_status

### Finance

- list_customer_invoices
- get_customer_financial_summary

Financial calculations use Decimal and derive
balances from invoice lines and payments.

## MCP Interface

Nine tools are registered:

1. get_customer
2. list_customers
3. get_customer_db
4. list_customers_db
5. get_customer_orders_db
6. get_order_details_db
7. get_inventory_status_db
8. list_customer_invoices_db
9. get_customer_financial_summary_db

The first two tools retain the original Day 1 in-memory
demonstration. Seven tools use PostgreSQL-backed adapters.

## Security

- PostgreSQL reader account: a04_reader
- Read-only database privileges
- Default-deny local role policy
- Tool-level permission checks
- Structured audit events on stderr
- Parameterized SQL
- Bounded customer and order queries

The local role is selected by a trusted process launcher.
It is not an authenticated remote identity.

This project is not yet production-hardened.

## Validation

Day 2 regression suite:

- 26 automated tests passed
- CRM, ERP and Finance integration verified
- MCP stdio communication verified
- Local policy decisions verified
- Database reader INSERT attempt denied

## Demonstration

With the local PostgreSQL container running:

    python -m src.client.enterprise_demo

The demonstration retrieves customer, order,
inventory and finance information through MCP.

## Future Improvements

- Authenticated identity propagation
- Durable audit storage and correlation IDs
- Structured output schemas for all tools
- Centralized policy enforcement in AI-A05
- A02 agent orchestration integration
- A03 RAG retrieval exposed through MCP
- Streamable HTTP deployment
- Full financial point-in-time semantics

## Limitations

The dataset is synthetic.

The governance implementation demonstrates policy
enforcement but is not production authentication.

The database schema and initial seed script have been
validated against the local PostgreSQL instance.

Existing payment totals are used when calculating
balances for an as-of date. Historical payment cutoffs
are not yet implemented.

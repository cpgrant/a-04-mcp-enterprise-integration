BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS crm;
CREATE SCHEMA IF NOT EXISTS erp;
CREATE SCHEMA IF NOT EXISTS finance;

-- ========================================
-- CRM
-- ========================================

CREATE TABLE IF NOT EXISTS crm.customers (
    customer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_code VARCHAR(20) UNIQUE NOT NULL,
    customer_name VARCHAR(200) NOT NULL,
    industry VARCHAR(100),
    country VARCHAR(2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active','inactive','prospect')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS crm.contacts (
    contact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL
        REFERENCES crm.customers(customer_id),
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255),
    job_title VARCHAR(100),
    is_primary BOOLEAN NOT NULL DEFAULT false
);

-- ========================================
-- ERP
-- ========================================

CREATE TABLE IF NOT EXISTS erp.products (
    product_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku VARCHAR(30) UNIQUE NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    unit_price NUMERIC(14,2) NOT NULL
        CHECK (unit_price >= 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    active BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS erp.sales_orders (
    order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(30) UNIQUE NOT NULL,
    customer_id UUID NOT NULL
        REFERENCES crm.customers(customer_id),
    order_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL
        CHECK (status IN (
            'pending','confirmed','shipped',
            'delivered','cancelled'
        )),
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS erp.order_lines (
    order_line_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL
        REFERENCES erp.sales_orders(order_id),
    product_id UUID NOT NULL
        REFERENCES erp.products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(14,2) NOT NULL
        CHECK (unit_price >= 0),
    line_total NUMERIC(14,2)
        GENERATED ALWAYS AS (quantity * unit_price) STORED
);

CREATE TABLE IF NOT EXISTS erp.inventory (
    product_id UUID PRIMARY KEY
        REFERENCES erp.products(product_id),
    quantity_on_hand INTEGER NOT NULL DEFAULT 0
        CHECK (quantity_on_hand >= 0),
    quantity_reserved INTEGER NOT NULL DEFAULT 0
        CHECK (quantity_reserved >= 0),
    reorder_level INTEGER NOT NULL DEFAULT 0
        CHECK (reorder_level >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (quantity_reserved <= quantity_on_hand)
);

-- ========================================
-- FINANCE
-- ========================================

CREATE TABLE IF NOT EXISTS finance.invoices (
    invoice_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_number VARCHAR(30) UNIQUE NOT NULL,
    order_id UUID NOT NULL
        REFERENCES erp.sales_orders(order_id),
    customer_id UUID NOT NULL
        REFERENCES crm.customers(customer_id),
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL
        CHECK (status IN (
            'draft','issued','partially_paid',
            'paid','overdue','void'
        )),
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    CHECK (due_date >= invoice_date)
);

CREATE TABLE IF NOT EXISTS finance.invoice_lines (
    invoice_line_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL
        REFERENCES finance.invoices(invoice_id),
    description VARCHAR(250) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(14,2) NOT NULL
        CHECK (unit_price >= 0),
    line_total NUMERIC(14,2)
        GENERATED ALWAYS AS (quantity * unit_price) STORED
);

CREATE TABLE IF NOT EXISTS finance.payments (
    payment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL
        REFERENCES finance.invoices(invoice_id),
    payment_date DATE NOT NULL,
    amount NUMERIC(14,2) NOT NULL
        CHECK (amount > 0),
    payment_method VARCHAR(30)
        CHECK (payment_method IN (
            'bank_transfer','card','other'
        )),
    reference VARCHAR(100)
);

-- ========================================
-- INDEXES
-- ========================================

CREATE INDEX IF NOT EXISTS idx_contacts_customer
    ON crm.contacts(customer_id);

CREATE INDEX IF NOT EXISTS idx_orders_customer
    ON erp.sales_orders(customer_id);

CREATE INDEX IF NOT EXISTS idx_orders_date
    ON erp.sales_orders(order_date);

CREATE INDEX IF NOT EXISTS idx_order_lines_order
    ON erp.order_lines(order_id);

CREATE INDEX IF NOT EXISTS idx_order_lines_product
    ON erp.order_lines(product_id);

CREATE INDEX IF NOT EXISTS idx_invoices_customer
    ON finance.invoices(customer_id);

CREATE INDEX IF NOT EXISTS idx_invoices_order
    ON finance.invoices(order_id);

CREATE INDEX IF NOT EXISTS idx_invoices_due
    ON finance.invoices(due_date);

CREATE INDEX IF NOT EXISTS idx_invoice_lines_invoice
    ON finance.invoice_lines(invoice_id);

CREATE INDEX IF NOT EXISTS idx_payments_invoice
    ON finance.payments(invoice_id);

COMMIT;

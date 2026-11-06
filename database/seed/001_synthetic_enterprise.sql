BEGIN;

-- CRM: 25 synthetic customers
INSERT INTO crm.customers
    (customer_code, customer_name, industry, country, status)
SELECT
    'C' || lpad(n::text, 3, '0'),
    CASE WHEN n = 1 THEN 'ACME Corporation'
         ELSE 'Synthetic Business ' || lpad(n::text, 3, '0')
    END,
    (ARRAY['Manufacturing','Technology','Logistics',
           'Healthcare','Retail'])[1 + (n % 5)],
    (ARRAY['DK','DE','FR','GB'])[1 + (n % 4)],
    'active'
FROM generate_series(1,25) AS n
ON CONFLICT (customer_code) DO NOTHING;

-- CRM: 40 contacts
INSERT INTO crm.contacts
    (customer_id, full_name, email, job_title, is_primary)
SELECT
    c.customer_id,
    'Contact ' || n,
    'contact' || n || '@example.test',
    CASE WHEN n % 2 = 0 THEN 'Operations Manager'
         ELSE 'Finance Manager' END,
    n <= 25
FROM generate_series(1,40) AS n
JOIN crm.customers c
  ON c.customer_code =
     'C' || lpad((((n-1) % 25)+1)::text,3,'0')
WHERE NOT EXISTS (
    SELECT 1 FROM crm.contacts x
    WHERE x.email = 'contact' || n || '@example.test'
);

-- ERP: 30 products
INSERT INTO erp.products
    (sku, product_name, category, unit_price)
SELECT
    'SKU-' || lpad(n::text,3,'0'),
    'Enterprise Product ' || n,
    (ARRAY['Hardware','Software','Services'])[1+(n%3)],
    (100 + n*35)::numeric(14,2)
FROM generate_series(1,30) AS n
ON CONFLICT (sku) DO NOTHING;

-- ERP: inventory with deliberate low-stock scenarios
INSERT INTO erp.inventory
    (product_id, quantity_on_hand,
     quantity_reserved, reorder_level)
SELECT
    p.product_id,
    CASE WHEN n % 6 = 0 THEN 4 ELSE 100 END,
    CASE WHEN n % 6 = 0 THEN 2 ELSE 15 END,
    20
FROM generate_series(1,30) AS n
JOIN erp.products p
  ON p.sku = 'SKU-' || lpad(n::text,3,'0')
ON CONFLICT (product_id) DO NOTHING;

-- ERP: 100 sales orders
INSERT INTO erp.sales_orders
    (order_number, customer_id, order_date, status)
SELECT
    'SO-' || lpad(n::text,4,'0'),
    c.customer_id,
    DATE '2026-08-01' + ((n*2) % 90),
    CASE
        WHEN n > 80 THEN 'cancelled'
        WHEN n % 4 = 0 THEN 'pending'
        WHEN n % 4 = 1 THEN 'confirmed'
        WHEN n % 4 = 2 THEN 'shipped'
        ELSE 'delivered'
    END
FROM generate_series(1,100) AS n
JOIN crm.customers c
  ON c.customer_code =
     'C' || lpad((((n-1)%25)+1)::text,3,'0')
ON CONFLICT (order_number) DO NOTHING;

-- ERP: two order lines per sales order
INSERT INTO erp.order_lines
    (order_id, product_id, quantity, unit_price)
SELECT
    o.order_id,
    p.product_id,
    1 + ((o_num + line_num) % 5),
    p.unit_price
FROM generate_series(1,100) AS o_num
CROSS JOIN generate_series(1,2) AS line_num
JOIN erp.sales_orders o
  ON o.order_number =
     'SO-' || lpad(o_num::text,4,'0')
JOIN erp.products p
  ON p.sku = 'SKU-' ||
     lpad(((((o_num-1)*2+line_num-1)%30)+1)::text,3,'0')
WHERE NOT EXISTS (
    SELECT 1 FROM erp.order_lines x
    WHERE x.order_id = o.order_id
      AND x.product_id = p.product_id
);

-- Finance: invoices for first 80 orders
INSERT INTO finance.invoices
    (invoice_number, order_id, customer_id,
     invoice_date, due_date, status)
SELECT
    'INV-' || lpad(n::text,4,'0'),
    o.order_id,
    o.customer_id,
    CASE WHEN n <= 55 THEN DATE '2026-09-01'
         ELSE DATE '2026-10-25' END,
    CASE WHEN n <= 55 THEN DATE '2026-10-01'
         ELSE DATE '2026-11-24' END,
    CASE
        WHEN n <= 25 THEN 'paid'
        WHEN n <= 40 THEN 'partially_paid'
        WHEN n <= 55 THEN 'overdue'
        ELSE 'issued'
    END
FROM generate_series(1,80) AS n
JOIN erp.sales_orders o
  ON o.order_number =
     'SO-' || lpad(n::text,4,'0')
ON CONFLICT (invoice_number) DO NOTHING;

-- Finance: invoice lines copied from corresponding orders
INSERT INTO finance.invoice_lines
    (invoice_id, description, quantity, unit_price)
SELECT
    i.invoice_id,
    p.product_name,
    ol.quantity,
    ol.unit_price
FROM finance.invoices i
JOIN erp.order_lines ol ON ol.order_id = i.order_id
JOIN erp.products p ON p.product_id = ol.product_id
WHERE NOT EXISTS (
    SELECT 1 FROM finance.invoice_lines x
    WHERE x.invoice_id = i.invoice_id
      AND x.description = p.product_name
);

-- Finance: 50 payment records
-- Paid invoices receive full payment.
-- Partially paid invoices receive 50%.
-- Some overdue invoices receive 20%.
INSERT INTO finance.payments
    (invoice_id, payment_date, amount,
     payment_method, reference)
SELECT
    i.invoice_id,
    DATE '2026-10-10',
    CASE
        WHEN n <= 25 THEN totals.total
        WHEN n <= 40 THEN round(totals.total * 0.5, 2)
        ELSE round(totals.total * 0.2, 2)
    END,
    'bank_transfer',
    'PAY-' || lpad(n::text,4,'0')
FROM generate_series(1,50) AS n
JOIN finance.invoices i
  ON i.invoice_number =
     'INV-' || lpad(n::text,4,'0')
CROSS JOIN LATERAL (
    SELECT sum(il.line_total) AS total
    FROM finance.invoice_lines il
    WHERE il.invoice_id = i.invoice_id
) totals
WHERE NOT EXISTS (
    SELECT 1 FROM finance.payments x
    WHERE x.reference = 'PAY-' || lpad(n::text,4,'0')
);

COMMIT;

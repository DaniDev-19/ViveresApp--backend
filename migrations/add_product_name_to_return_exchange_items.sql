-- Migration: Add product_name column to return and exchange items
-- Run this in PostgreSQL to add the denormalized product_name column

-- 1. Add product_name to sale_return_items
ALTER TABLE sale_return_items 
ADD COLUMN IF NOT EXISTS product_name VARCHAR(255);

-- Populate existing records from product relationship
UPDATE sale_return_items 
SET product_name = p.name
FROM products p
WHERE sale_return_items.product_id = p.id
AND sale_return_items.product_name IS NULL;

-- 2. Add product_name to sale_exchange_items_out
ALTER TABLE sale_exchange_items_out 
ADD COLUMN IF NOT EXISTS product_name VARCHAR(255);

-- Populate existing records from product relationship
UPDATE sale_exchange_items_out 
SET product_name = p.name
FROM products p
WHERE sale_exchange_items_out.product_id = p.id
AND sale_exchange_items_out.product_name IS NULL;

-- 3. Add product_name to sale_exchange_items_in
ALTER TABLE sale_exchange_items_in 
ADD COLUMN IF NOT EXISTS product_name VARCHAR(255);

-- Populate existing records from product relationship
UPDATE sale_exchange_items_in 
SET product_name = p.name
FROM products p
WHERE sale_exchange_items_in.product_id = p.id
AND sale_exchange_items_in.product_name IS NULL;

-- Verify
SELECT 'sale_return_items' as table_name, count(*) as total, count(product_name) as with_name FROM sale_return_items
UNION ALL
SELECT 'sale_exchange_items_out', count(*), count(product_name) FROM sale_exchange_items_out
UNION ALL
SELECT 'sale_exchange_items_in', count(*), count(product_name) FROM sale_exchange_items_in;
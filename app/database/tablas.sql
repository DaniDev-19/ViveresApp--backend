-- ==============================================================================
-- ESQUEMA DE BASE DE DATOS: VÍVERES VALENTINA
-- SCRIPT MAESTRO CONSOLIDADO (16+ TABLAS)
-- Incluye índices de optimización y restricciones
-- ==============================================================================

-- 1. USUARIOS
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) DEFAULT 'worker' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 2. CATEGORÍAS
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);
CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(name);

-- 3. PRODUCTOS
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    barcode VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    cost_price DOUBLE PRECISION NOT NULL,               -- Precio de costo en USD
    profit_margin DOUBLE PRECISION DEFAULT 0.30,        -- Margen predeterminado 30%
    tax_rate DOUBLE PRECISION DEFAULT 0.16,             -- IVA predeterminado 16%
    price_usd DOUBLE PRECISION NOT NULL,                -- Precio de venta calculado
    stock_quantity INTEGER DEFAULT 0,
    min_stock_level INTEGER DEFAULT 5,                  -- Nivel de stock crítico
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    image_url TEXT,
    is_public BOOLEAN DEFAULT TRUE                      -- Visible en el catálogo web
);
CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);

-- 4. PROVEEDORES
CREATE TABLE IF NOT EXISTS providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    rif VARCHAR(100) UNIQUE,
    contact_info TEXT
);
CREATE INDEX IF NOT EXISTS idx_providers_name ON providers(name);
CREATE INDEX IF NOT EXISTS idx_providers_rif ON providers(rif);

-- 5. ÓRDENES DE COMPRA
CREATE TABLE IF NOT EXISTS purchase_orders (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER REFERENCES providers(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expected_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'draft',
    notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_provider ON purchase_orders(provider_id);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status);

-- 6. ÍTEMS DE COMPRA
CREATE TABLE IF NOT EXISTS purchase_items (
    id SERIAL PRIMARY KEY,
    purchase_id INTEGER REFERENCES purchase_orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    product_name VARCHAR(255),
    requested_quantity INTEGER NOT NULL,
    received_quantity INTEGER DEFAULT 0,
    cost_price DOUBLE PRECISION,
    status VARCHAR(50) DEFAULT 'pending'
);
CREATE INDEX IF NOT EXISTS idx_purchase_items_order ON purchase_items(purchase_id);
CREATE INDEX IF NOT EXISTS idx_purchase_items_product ON purchase_items(product_id);

-- 7. CLIENTES
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    cedula VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    email VARCHAR(255),
    address TEXT
);
CREATE INDEX IF NOT EXISTS idx_customers_cedula ON customers(cedula);
CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);

-- 8. VENTAS
CREATE TABLE IF NOT EXISTS sales (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_amount_usd DOUBLE PRECISION NOT NULL,
    total_tax_usd DOUBLE PRECISION DEFAULT 0.0,
    has_delivery BOOLEAN DEFAULT FALSE,
    delivery_amount_usd DOUBLE PRECISION DEFAULT 0.0,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'completed'
);
CREATE INDEX IF NOT EXISTS idx_sales_created_at ON sales(created_at);
CREATE INDEX IF NOT EXISTS idx_sales_user ON sales(user_id);
CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_sales_status ON sales(status);

-- 9. ÍTEMS DE VENTA
CREATE TABLE IF NOT EXISTS sale_items (
    id SERIAL PRIMARY KEY,
    sale_id INTEGER REFERENCES sales(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL,
    unit_price_usd DOUBLE PRECISION NOT NULL,
    tax_rate DOUBLE PRECISION NOT NULL,
    applied_margin DOUBLE PRECISION
);
CREATE INDEX IF NOT EXISTS idx_sale_items_sale ON sale_items(sale_id);
CREATE INDEX IF NOT EXISTS idx_sale_items_product ON sale_items(product_id);

-- 10. PAGOS
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    sale_id INTEGER REFERENCES sales(id) ON DELETE CASCADE,
    method VARCHAR(100) NOT NULL,
    amount DOUBLE PRECISION NOT NULL,                     -- Monto en moneda original
    currency VARCHAR(10) NOT NULL,                       -- VES, USD, COP, etc.
    exchange_rate DOUBLE PRECISION DEFAULT 1.0,           -- Tasa utilizada
    amount_usd_equivalent DOUBLE PRECISION NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_payments_sale ON payments(sale_id);
CREATE INDEX IF NOT EXISTS idx_payments_method ON payments(method);

-- 11. PEDIDOS WEB (Pedidos Públicos)
CREATE TABLE IF NOT EXISTS web_orders (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    customer_data JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending_review',
    total_estimated_usd DOUBLE PRECISION NOT NULL,
    payment_method VARCHAR(100),
    payment_proof_url TEXT,                               -- URL de comprobante (S3/R2)
    transaction_ref VARCHAR(255)
);
CREATE INDEX IF NOT EXISTS idx_web_orders_status ON web_orders(status);
CREATE INDEX IF NOT EXISTS idx_web_orders_customer ON web_orders(customer_id);

-- 12. ÍTEMS DE PEDIDO WEB
CREATE TABLE IF NOT EXISTS web_order_items (
    id SERIAL PRIMARY KEY,
    web_order_id INTEGER REFERENCES web_orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    product_name VARCHAR(255),
    quantity INTEGER NOT NULL,
    price_usd DOUBLE PRECISION NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_web_order_items_order ON web_order_items(web_order_id);

-- 13. NOTIFICACIONES
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'info',                      -- info, success, warning, danger
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
);
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(is_read) WHERE is_read = FALSE;

-- 14. AUDITORÍAS (Logs)
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,                         -- CREATE, UPDATE, DELETE, LOGIN
    table_name VARCHAR(100),
    details TEXT,                                         -- Descripción o JSON
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);

-- 15. TASAS DE CAMBIO
CREATE TABLE IF NOT EXISTS exchange_rates (
    id SERIAL PRIMARY KEY,
    currency VARCHAR(20) NOT NULL,                         -- BCV, USDT, COP
    rate DOUBLE PRECISION NOT NULL,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_exchange_rates_currency ON exchange_rates(currency);

-- 16. AJUSTES DE INVENTARIO
CREATE TABLE IF NOT EXISTS inventory_adjustments (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    quantity_change INTEGER NOT NULL,
    reason VARCHAR(255),                                  -- 'robo', 'daño', 'correccion', 'devolucion'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_inv_adj_product ON inventory_adjustments(product_id);

-- ==============================================================================
-- DISPARADORES Y FUNCIONES (TRADUCIDOS)
-- ==============================================================================

-- Función para actualizar el precio del producto automáticamente cuando cambie el costo o margen
CREATE OR REPLACE FUNCTION actualizar_precio_producto()
RETURNS TRIGGER AS $$
BEGIN
    NEW.price_usd = NEW.cost_price * (1 + NEW.profit_margin);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_actualizar_precio ON products;
CREATE TRIGGER trg_actualizar_precio
BEFORE INSERT OR UPDATE OF cost_price, profit_margin ON products
FOR EACH ROW EXECUTE FUNCTION actualizar_precio_producto();

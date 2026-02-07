# 📖 Wiki Técnica - Backend: Viveres App

Esta Wiki proporciona detalles profundos sobre el funcionamiento interno del servidor de **Viveres App**.

Arquitecto de Solución: **DaniDev**

---

## 💾 Modelo de Datos - Base de Datos (PostgreSQL)

El sistema utiliza un esquema relacional optimizado con las siguientes entidades principales (16 tablas):

### Entidades Core
| Tabla | Propósito |
|---|---|
| `users` | Gestión de administradores, cajeros y personal de inventario. |
| `products` | Catálogo maestro de productos con códigos de barra, precios en USD y toggles de IVA web. |
| `customers` | Registro de clientes (cédula, nombre, contacto) para ventas y pedidos. |

### Operaciones Financieras
| Tabla | Propósito |
|---|---|
| `sales` | Cabecera de transacciones completadas. |
| `sale_items` | Detalles de cada ítem vendido (captura precio y margen histórico). |
| `payments` | Registro multimoneda (USD, BS, COP) de cada pago de una venta. |
| `exchange_rates` | Historial de tasas de cambio (BCV, Paralelo, etc.). |

### Flujo de Compras e Inventario
| Tabla | Propósito |
|---|---|
| `providers` | Listado de proveedores y sus RIF. |
| `purchase_orders` | Órdenes generadas para reponer stock. |
| `purchase_items` | Productos solicitados vs. productos recibidos. |
| `inventory_adjustments` | Registro de mermas, robos o devoluciones. |

---

## 📈 Lógica de Reportes y Cálculos

### Cálculo de Ganancia
La ganancia no es simplemente estática. Se calcula en el servidor mediante:
`Ganancia = ∑ (Precio_Venta_USD - Precio_Costo_USD) * Cantidad_Vendida`
Esto permite ver la utilidad neta real descontando el costo del producto al momento de la venta.

### Conversión de Moneda
El sistema calcula el total en Bolívares (BS) dinámicamente:
`Total_BS = Total_Venta_USD * Mayor_Tasa_Aplicada_en_Pagos`
Esto garantiza que el reporte refleje la realidad de los pagos recibidos si hubo múltiples divisas.

---

## 📡 Endpoints Estratégicos (`/api/v1`)

### `/reports`
- `GET /sales/export`: Genera reportes detallados en PDF (ReportLab) o Excel (OpenPyxl) con filtros de fecha. Incluye totales de IVA y Ganancias.
- `GET /inventory/export`: Genera listado de existencias con valorización de inventario.

### `/pos` (en `/sales`)
- `POST /`: Registra una nueva venta, resta stock automáticamente, crea registros de pago y genera el comprobante digital.

---

## 🛠️ Automatizaciones (Triggers)
Hemos implementado disparadores en SQL para minimizar errores humanos:
- **`trg_actualizar_precio`**: Siempre que se modifica el costo de un producto o su margen, la base de datos recalcula el `price_usd` instantáneamente.

---

## 🛡️ Mejores Prácticas de Ingeniería
- **Manejo de Errores Global:** Todos los errores se capturan y devuelven en formato JSON estandarizado para que el frontend pueda mostrarlos amigablemente.
- **Transacciones CRUD:** Se utilizan transacciones ACID para asegurar que, si falla el registro de un pago, no se descuente el stock del producto erróneamente.

---

© 2026 - **Viveres App Wiki** | **DaniDev software Engineer**

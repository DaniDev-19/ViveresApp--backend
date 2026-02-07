# 🛒 Viveres App - Backend API (Pos & Inventory System)

Este es el núcleo de procesamiento de **Viveres App**, un sistema robusto de Punto de Venta (POS), Gestión de Inventario y Pedidos Públicos diseñado para alta eficiencia y escalabilidad.

Desarrollado y Arquitectado por: **DaniDev - Software Engineer**

---

## 🛠️ Stack Tecnológico

La arquitectura está basada en el concepto de **Async Fast-API Architecture**, priorizando el rendimiento no bloqueante y la integridad de datos.

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+)
- **Base de Datos:** PostgreSQL
- **ORM:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Async Engine)
- **Migraciones:** Alembic
- **Validación de Datos:** Pydantic V2
- **Almacenamiento:** Cloudflare R2 (S3 API) + Local Storage (Patrón Strategy)
- **Reportes:** ReportLab (PDF) & OpenPyxl (Excel)
- **Seguridad:** JWT (JSON Web Tokens) & Passlib (Bcrypt)

---

## 🏗️ Estructura de Carpetas

El proyecto sigue el patrón de diseño **Layered Architecture** (Arquitectura por Capas) para separar responsabilidades.

```text
backend/
├── app/
│   ├── api/                # Capa de Controladores (Endpoints)
│   │   └── v1/             # Versión 1 de la API
│   ├── core/               # Configuraciones Globales (JWT, Seguridad, Constantes)
│   ├── db/                 # Sesión de BD y Clase Base
│   ├── database/           # Scripts SQL Maestros y Migraciones
│   ├── models/             # Modelos de SQLAlchemy (Tablas)
│   ├── schemas/            # Pydantic Models (Input/Output Validation)
│   ├── services/           # Lógica de Negocio (Generación de reportes, cálculos complejos)
│   └── main.py             # Punto de entrada de la aplicación
├── alembic/                # Historial de migraciones de base de datos
├── requirements.txt        # Dependencias del sistema
└── .env                    # Variables de entorno (No incluido por seguridad)
```

---

## 🔒 Implementación de Seguridad

La seguridad es el pilar de **Viveres App**. Hemos implementado estándares de nivel industrial:

1. **Autenticación JWT:** Utiliza tokens firmados con algoritmos asimétricos para validar sesiones. Los tokens tienen un tiempo de expiración (TTL) controlado.
2. **Hashing de Contraseñas:** Ninguna contraseña se guarda en texto plano. Usamos **Bcrypt** con un factor de trabajo alto para prevenir ataques de fuerza bruta.
3. **CORS (Cross-Origin Resource Sharing):** Configurado estrictamente para permitir solo el dominio autorizado del frontend.
4. **Validación de Tipos (Sanitización):** Gracias a Pydantic, todos los inputs son validados y sanitizados antes de llegar a la lógica de negocio, previniendo inyecciones y datos malformados.
5. **SQL Injection Prevention:** SQLAlchemy utiliza consultas parametrizadas por defecto, eliminando el riesgo de inyecciones SQL.

---

## ✨ Buenas Prácticas Aplicadas

- **Dependency Injection (DI):** Utilizamos el sistema de inyección de dependencias de FastAPI para gestionar sesiones de base de datos (`get_db`) de forma eficiente.
- **Async/Await Everywhere:** Todas las llamadas a Base de Datos y Procesamiento de I/O son asíncronas para maximizar el throughput del servidor.
- **Eager Loading:** Optimización de consultas SQL mediante `joinedload` y `selectinload` para evitar el problema de N+1 consultas.
- **Separación de Concernientes:** La lógica de generación de archivos (PDF/Excel) reside en `services`, fuera de los controladores.

---

## 🚀 Instalación y Ejecución

1. ** Clonar y Entorno Virtual:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

2. **Instalar Dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Variables de Entorno (.env):**
   Configura tu archivo local basado en los requerimientos del sistema:
   ```env
   # Core
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/viveres_db
   SECRET_KEY=tu_super_secreto
   
   # Storage (Strategy: local | r2)
   STORAGE_MODE=r2
   R2_BUCKET=tu-bucket
   R2_ACCESS_KEY=xxx
   R2_SECRET_KEY=xxx
   R2_ENDPOINT=https://xxx.r2.cloudflarestorage.com
   R2_PUBLIC_URL=https://pub-xxx.r2.dev
   
   # White-Label Config
   BUSINESS_NAME="Mi Negocio"
   BUSINESS_PHONE="+584120000000"
   BUSINESS_ADDRESS="Calle Falsa 123"
   ```

4. **Levantar el Servidor:**
   ```bash
   uvicorn app.main:app --reload
   ```

---

## 📑 Documentación de la API

Una vez ejecutado, puedes acceder a la interfaz interactiva (Swagger UI) en:
`http://localhost:8000/docs`

---

© 2026 - Proyecto **Viveres App** | Desarrollado por **DaniDev**

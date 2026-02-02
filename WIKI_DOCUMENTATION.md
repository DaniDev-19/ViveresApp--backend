# 📚 ViveresApp Backend - Documentación Técnica (Wiki)

Este documento sirve como bitácora técnica y guía profunda del desarrollo del backend de ViveresApp.

## 🏗️ Arquitectura y Decisiones de Diseño

### 1. Stack Tecnológico
Elegimos **FastAPI** por su rendimiento asíncrono y generación automática de documentación. La base de datos es **PostgreSQL** para garantizar integridad transaccional, vital en sistemas contables y de inventario.

*   **ORM Asíncrono**: Usamos `SQLAlchemy 2.0` con `asyncpg`. Esto permite manejar miles de conexiones concurrentes sin bloquear el hilo principal, ideal para un POS con múltiples cajas.
*   **Validación Estricta**: `Pydantic` asegura que nunca entren datos corruptos al sistema. Si el frontend envía un precio negativo o un email inválido, el backend lo rechaza instantáneamente (422 Unprocessable Entity).

### 2. Estructura Modular
El proyecto no es un monolito desordenado. Se dividió en capas claras:
*   `endpoints/`: Solo manejan la entrada HTTP y retornan respuestas. No contienen lógica de negocio compleja.
*   `services/`: Aquí vive la "inteligencia". `currency_service`, `pdf_generator`, `image_service`. Son reutilizables y testearles independientemente.
*   `models/` & `schemas/`: Separación estricta entre **Entidades de BD** (Tablas) y **Objetos de Transferencia** (JSON). Esto evita exponer datos sensibles (como passwords o campos internos) por accidente.

### D. Seguridad, Roles (RBAC) y Auditoría
*   **JWT & OAuth2**: Implementamos un sistema de autenticación centralizado en `app/api/deps.py`. Los tokens tienen expiración configurable y se verifican en cada petición sensible.
*   **Roles Dinámicos**: El sistema soporta `admin` y `worker`. El decorador `Depends(deps.get_current_active_user)` asegura que no solo el token sea válido, sino que el usuario tenga los permisos necesarios.
*   **Auditoría (Bitácora)**: Cada acción de escritura (POST, PUT, DELETE) invoca a `AuditService.log_action`, grabando el ID del usuario real, la tabla afectada y los detalles de la operación.
*   **CORS**: Configurado dinámicamente en `app/main.py`. Permite orígenes específicos definidos en la variable de entorno `BACKEND_CORS_ORIGINS`.

## 🛠️ Bitácora de Comandos

Estos son los comandos clave utilizados durante el desarrollo y para mantenimiento:

### 1. Inicialización de Entorno
Es importante ubicarse dentro de la carpeta `backend` antes de ejecutar cualquier comando.

```bash
# Entrar a la carpeta del proyecto
cd backend

# Crear entorno virtual
python -m venv .venv

# Activar (Windows PowerShell)
.venv\Scripts\activate

# Instalar dependencias completas
pip install -r requirements.txt
```

### 2. Base de Datos (Alembic)
Cada vez que modificamos un modelo (`models/`), corremos estos comandos. ¡No tocamos SQL a mano!

```bash
# Crear una nueva migración (detecta cambios automáticamente)
alembic revision --autogenerate -m "descripcion_del_cambio"

# Aplicar cambios a la BD
alembic upgrade head
```

### 3. Configuración (.env)
Asegúrate de tener un archivo `.env` configurado. Puedes usar `.env.example` como base.

```bash
# Ejemplo de configuración necesaria
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname
SECRET_KEY=tu_clave_secreta_para_jwt
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
```

## 🔮 Futuro y Escalabilidad

El backend está listo para crecer:
1.  **Caché**: Implementación de Redis para tasas de cambio volátiles.
2.  **Webhooks**: Notificaciones automáticas a servicios externos tras una venta.
3.  **Dockerización**: Uso de `Dockerfile` para despliegues en la nube (AWS/GCP/Heroku).

---

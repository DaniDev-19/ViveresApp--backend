from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "ViveresApp"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/viveres_app"
    )

    # Security
    SECRET_KEY: str = "your-super-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.31.170:3000"
    ]

    # Business Information
    BUSINESS_NAME: str = "Víveres Valentina"
    BUSINESS_RIF: str = "J-00000000-0"
    BUSINESS_PHONE: str = "+58 000 0000000"
    BUSINESS_ADDRESS: str = "Dirección del Negocio"
    BUSINESS_EMAIL: str = "contacto@ejemplo.com"

    # Payment QR Information
    PAGO_MOVIL_BANCO: str = "0102"
    PAGO_MOVIL_TELEFONO: str = "+58 000 0000000"
    PAGO_MOVIL_RIF_CI: str = "V-00000000"
    PAGO_MOVIL_NOMBRE: str = "Víveres Valentina"
    PAYPAL_CORREO: str = "contacto@ejemplo.com"
    BINANCE_PAY_ID: str = "000000000"
    ZINLI_CORREO: str = "contacto@ejemplo.com"
    AIRTM_CORREO: str = "contacto@ejemplo.com"

    # Storage Settings
    STORAGE_MODE: str = "local"  # "local" or "r2"
    R2_BUCKET: Optional[str] = None
    R2_ACCESS_KEY: Optional[str] = None
    R2_SECRET_KEY: Optional[str] = None
    R2_ENDPOINT: Optional[str] = None
    R2_PUBLIC_URL: Optional[str] = None

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
Settings.model_rebuild()

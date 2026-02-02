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
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()

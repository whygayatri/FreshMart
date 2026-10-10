from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings and environment configuration.
    """
    APP_NAME: str = "FreshMart Grocery"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security & Sessions
    SECRET_KEY: str = "development-insecure-secret-key-change-in-production-123456789"
    COOKIE_SECURE: bool = False
    SESSION_COOKIE_NAME: str = "grocery_session"
    CSRF_COOKIE_NAME: str = "grocery_csrf"
    SESSION_EXPIRE_HOURS: int = 24

    # Database
    DATABASE_URL: str = "sqlite:///./grocery.db"

    # Default / Development Admin Credentials
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@freshmart.local"
    ADMIN_PASSWORD: str = "Admin@12345"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance to avoid re-reading configuration on every call.
    """
    return Settings()

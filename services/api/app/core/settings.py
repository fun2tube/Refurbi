from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://refurbi:refurbi_dev_password@localhost:5432/refurbi"
    # Auth. The JWT secret default is a dev-only placeholder; set a real one outside dev.
    jwt_secret: str = "dev-only-change-me-dev-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30
    refresh_cookie_name: str = "refurbi_refresh"
    # Super admin seeded by `python -m app.seed` (both must be set).
    super_admin_email: str = ""
    super_admin_password: str = ""
    # Default page size / cap for list endpoints.
    default_page_size: int = 20
    max_page_size: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()

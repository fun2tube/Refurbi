from functools import lru_cache

from pydantic import field_validator
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
    # IMEI protection. Dev-only placeholders; set real keys outside dev (see .env.example).
    # imei_encryption_keys: comma-separated Fernet keys, newest first (older ones decrypt only).
    imei_encryption_keys: str = "ZGV2LW9ubHktaW1laS1rZXktZGV2LW9ubHkta2V5MDA="
    imei_hash_key: str = "dev-only-imei-hash-key-change-me"
    # Comma-separated browser origins allowed by CORS (the web app). Scheme optional: a bare
    # host (as some hosting platforms provide) is treated as https.
    cors_origins: str = ""
    # Always allowed: the Render preview web app (no cross-service env reference needed).
    default_cors_origins: str = "https://refurbi-web.onrender.com"
    # Regex for preview deploys / renamed services of the same app.
    cors_origin_regex: str = r"^https://refurbi-web[a-z0-9-]*\.onrender\.com$"
    # Image storage: local disk in dev; s3 = Cloudflare R2 free tier (S3-compatible).
    storage_backend: str = "local"
    media_dir: str = "media"
    s3_endpoint: str = ""
    s3_bucket: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_public_base: str = ""
    # Default page size / cap for list endpoints.
    default_page_size: int = 20
    max_page_size: int = 100

    @field_validator("database_url")
    @classmethod
    def _normalise_db_url(cls, v: str) -> str:
        # Hosts hand out postgres:// or postgresql://; SQLAlchemy needs the psycopg driver.
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                return "postgresql+psycopg://" + v[len(prefix) :]
        return v

    @property
    def is_preview(self) -> bool:
        return self.app_env == "preview"

    @property
    def cors_origin_list(self) -> list[str]:
        out: list[str] = []
        for raw in f"{self.default_cors_origins},{self.cors_origins}".split(","):
            o = raw.strip().rstrip("/")
            if not o:
                continue
            o = o if "://" in o else f"https://{o}"
            if o not in out:
                out.append(o)
        return out


@lru_cache
def get_settings() -> Settings:
    return Settings()

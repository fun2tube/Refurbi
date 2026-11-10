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
    # Seller / invoice details. FOUNDER INPUT: all are labelled placeholders until real values
    # are provided (GSTIN, legal name, address, state code, GST rate for the margin scheme).
    # Email (Brevo free tier). Empty key = fake outbox adapter (dev/tests/preview).
    brevo_api_key: str = ""
    email_from: str = "no-reply@example.invalid"
    # Payments: empty razorpay_key_id = fake gateway (dev/tests/preview). Never commit real keys.
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = "dev-only-webhook-secret"
    reservation_hours: int = 24
    # PLACEHOLDER return window (days after delivery). FOUNDER INPUT: real returns policy.
    return_window_days: int = 7
    otp_ttl_minutes: int = 10
    seller_legal_name: str = "REFURBI DEMO TRADERS (placeholder - not a real entity)"
    seller_gstin: str = "00AAAAA0000A0Z0"
    seller_address: str = "Placeholder address - to be confirmed by founder"
    seller_state_code: str = "29"
    invoice_prefix: str = "DEMO"
    gst_rate_bps: int = 1800  # 18% - CA to confirm for refurbished phones / margin scheme
    hsn_code: str = "8517"
    default_gst_mode: str = "MARGIN"  # MARGIN | STANDARD (CA to confirm)
    # Static UPI ID for counter QR payments. FOUNDER INPUT; placeholder is not a real VPA.
    upi_id: str = "demo@upi"
    upi_payee_name: str = "Refurbi Demo"
    # FOUNDER INPUT: warranty months per sale. Placeholder until warranty terms are confirmed.
    warranty_months: int = 6
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

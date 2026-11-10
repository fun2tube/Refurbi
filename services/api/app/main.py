from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.catalog.router import admin as catalog_admin
from app.catalog.router import public as catalog_public
from app.core.errors import install_error_handlers
from app.core.logging import configure_logging, install_request_logging
from app.core.settings import get_settings
from app.storefront.router import router as storefront_router

configure_logging(get_settings().log_level)

app = FastAPI(title="Refurbi API", version="0.1.0")
install_error_handlers(app)
install_request_logging(app)
_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origin_list,
    allow_origin_regex=_settings.cors_origin_regex or None,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth_router)
app.include_router(catalog_public)
app.include_router(catalog_admin)
app.include_router(storefront_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

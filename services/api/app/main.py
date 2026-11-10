from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.catalog.router import admin as catalog_admin
from app.catalog.router import public as catalog_public
from app.core.errors import install_error_handlers
from app.core.logging import configure_logging, install_request_logging
from app.core.settings import get_settings

configure_logging(get_settings().log_level)

app = FastAPI(title="Refurbi API", version="0.1.0")
install_error_handlers(app)
install_request_logging(app)
app.include_router(auth_router)
app.include_router(catalog_public)
app.include_router(catalog_admin)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

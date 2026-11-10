from fastapi import FastAPI

from app.core.errors import install_error_handlers
from app.core.logging import configure_logging, install_request_logging
from app.core.settings import get_settings

configure_logging(get_settings().log_level)

app = FastAPI(title="Refurbi API", version="0.1.0")
install_error_handlers(app)
install_request_logging(app)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

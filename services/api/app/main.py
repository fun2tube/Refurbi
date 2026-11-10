from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.billing.router import router as billing_router
from app.catalog.router import admin as catalog_admin
from app.catalog.router import public as catalog_public
from app.commission.router import admin as commission_admin
from app.commission.router import partner as commission_partner
from app.core.errors import install_error_handlers
from app.core.logging import configure_logging, install_request_logging
from app.core.settings import get_settings
from app.counters.router import router as counters_router
from app.exchange.router import admin as exchange_admin
from app.exchange.router import public as exchange_public
from app.inventory.router import router as inventory_router
from app.pos.router import router as pos_router
from app.pricing.router import router as pricing_router
from app.procurement.router import router as procurement_router
from app.qc.router import media as media_router
from app.qc.router import router as qc_router
from app.storefront.router import router as storefront_router
from app.transfers.router import router as transfers_router
from app.warranty.router import admin as warranty_admin
from app.warranty.router import public as warranty_public

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
app.include_router(procurement_router)
app.include_router(qc_router)
app.include_router(counters_router)
app.include_router(inventory_router)
app.include_router(pricing_router)
app.include_router(media_router)
app.include_router(exchange_public)
app.include_router(exchange_admin)
app.include_router(transfers_router)
app.include_router(billing_router)
app.include_router(pos_router)
app.include_router(commission_admin)
app.include_router(commission_partner)
app.include_router(warranty_public)
app.include_router(warranty_admin)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

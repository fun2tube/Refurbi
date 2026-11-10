from sqlalchemy import select
from sqlalchemy.orm import Session

from app.catalog.models import ProductVariant
from app.commission.models import CommissionEntry
from app.counters.models import CommissionRule, commission_for
from app.inventory.models import Device
from app.pos.models import Sale


def record_commission(db: Session, sale: Sale, device: Device) -> CommissionEntry:
    """Freeze the commission for a sale using the counter's rules at sale time (caller commits)."""
    model_id = db.scalar(
        select(ProductVariant.model_id).where(ProductVariant.id == device.variant_id)
    )
    rules = list(
        db.scalars(select(CommissionRule).where(CommissionRule.counter_id == sale.counter_id))
    )
    e = CommissionEntry(
        sale_id=sale.id,
        counter_id=sale.counter_id,
        sale_price_paise=sale.price_paise,
        amount_paise=commission_for(rules, model_id, sale.price_paise),
    )
    db.add(e)
    db.flush()
    return e

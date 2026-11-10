import calendar
from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.pos.models import Sale
from app.warranty.models import Warranty


def add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y, m = d.year + m // 12, m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def create_warranty(db: Session, sale: Sale, today: date | None = None) -> Warranty:
    """Auto-create the warranty for a sale (caller commits). Starts on the sale date."""
    today = today or datetime.now(UTC).date()
    months = get_settings().warranty_months
    w = Warranty(
        sale_id=sale.id,
        invoice_id=sale.invoice_id,
        device_id=sale.device_id,
        months=months,
        starts_on=today,
        ends_on=add_months(today, months),
    )
    db.add(w)
    db.flush()
    return w

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.billing import gst
from app.billing.models import Invoice, InvoiceSequence
from app.catalog.models import Brand, ProductModel, ProductVariant
from app.core.errors import AppError, ConflictError, NotFoundError
from app.core.settings import get_settings
from app.inventory.models import Device

_IST = timedelta(hours=5, minutes=30)


def next_number(db: Session, fy: str) -> int:
    """Allocate the next gap-free number inside the caller's transaction (row-locked).

    If the caller rolls back, the allocation rolls back too, so numbers never skip.
    """
    row = db.scalar(select(InvoiceSequence).where(InvoiceSequence.fy == fy).with_for_update())
    if row is None:
        row = InvoiceSequence(fy=fy, last_no=0)
        db.add(row)
        db.flush()
    row.last_no += 1
    db.flush()
    return row.last_no


def issue_invoice(
    db: Session,
    device_id: int,
    *,
    selling_paise: int,
    customer_name: str,
    customer_phone: str,
    customer_state_code: str | None = None,
    mode: str = gst.MARGIN,
    counter_id: int | None = None,
    when: datetime | None = None,
) -> Invoice:
    """Create an invoice (caller commits). Refurbished second-hand devices default to MARGIN."""
    st = get_settings()
    d = db.get(Device, device_id)
    if d is None:
        raise NotFoundError("Device not found")
    if db.scalar(select(Invoice.id).where(Invoice.device_id == device_id)):
        raise ConflictError("This device already has an invoice", code="already_invoiced")
    if not customer_name.strip() or not customer_phone.strip():
        raise AppError("Customer name and phone are required", code="invalid_customer")
    state = customer_state_code or st.seller_state_code
    when = when or datetime.now(UTC)
    tax = gst.compute(
        mode,
        selling_paise=selling_paise,
        purchase_paise=d.cost_paise,
        rate_bps=st.gst_rate_bps,
        intra_state=state == st.seller_state_code,
    )
    fy = gst.financial_year(when.astimezone(UTC) + _IST)
    seq = next_number(db, fy)
    row = db.execute(
        select(Brand.name, ProductModel.name, ProductVariant.storage_gb, ProductVariant.color)
        .join(ProductModel, ProductModel.brand_id == Brand.id)
        .join(ProductVariant, ProductVariant.model_id == ProductModel.id)
        .where(ProductVariant.id == d.variant_id)
    ).first()
    desc = "Refurbished smartphone"
    if row:
        desc = (
            f"{row[0]} {row[1]} {row[2]}GB {row[3] or ''}".strip()
            + f" (IMEI ending {d.imei_last4})"
        )
    inv = Invoice(
        number=f"{st.invoice_prefix}/{fy}/{seq:06d}",
        fy=fy,
        seq=seq,
        device_id=device_id,
        counter_id=counter_id,
        mode=mode,
        customer_name=customer_name.strip(),
        customer_phone=customer_phone.strip(),
        customer_state_code=state,
        description=desc[:255],
        hsn_code=st.hsn_code,
        rate_bps=st.gst_rate_bps,
        total_paise=tax.total_paise,
        taxable_paise=tax.taxable_paise,
        cgst_paise=tax.cgst_paise,
        sgst_paise=tax.sgst_paise,
        igst_paise=tax.igst_paise,
        margin_paise=tax.margin_paise,
        seller={
            "name": st.seller_legal_name,
            "gstin": st.seller_gstin,
            "address": st.seller_address,
            "state_code": st.seller_state_code,
        },
    )
    db.add(inv)
    db.flush()
    return inv

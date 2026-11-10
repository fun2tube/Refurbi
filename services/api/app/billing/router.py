from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import has_permission, require_permission
from app.auth.models import User
from app.billing.models import Invoice
from app.billing.pdf import render_pdf
from app.core.db import get_session
from app.core.errors import ForbiddenError, NotFoundError

router = APIRouter(prefix="/admin/invoices", tags=["invoices"])
_read = Depends(require_permission("sales.read"))


def _out(i: Invoice) -> dict:
    return {
        "id": i.id,
        "number": i.number,
        "mode": i.mode,
        "device_id": i.device_id,
        "counter_id": i.counter_id,
        "customer_name": i.customer_name,
        "customer_phone": i.customer_phone,
        "description": i.description,
        "hsn_code": i.hsn_code,
        "total_paise": i.total_paise,
        "taxable_paise": i.taxable_paise,
        "cgst_paise": i.cgst_paise,
        "sgst_paise": i.sgst_paise,
        "igst_paise": i.igst_paise,
        "created_at": i.created_at,
    }


def _own(user: User, i: Invoice) -> Invoice:
    """Counter-scoped users only see their own counter's invoices."""
    if not has_permission(user, "sales.read", None) and not has_permission(
        user, "sales.read", i.counter_id
    ):
        raise ForbiddenError("You do not have permission to view this invoice")
    return i


@router.get("")
def list_invoices(user: User = _read, db: Session = Depends(get_session)) -> list[dict]:
    rows = db.scalars(select(Invoice).order_by(Invoice.id.desc()).limit(200))
    out = []
    for i in rows:
        try:
            out.append(_out(_own(user, i)))
        except ForbiddenError:
            continue
    return out


def _get(db: Session, user: User, iid: int) -> Invoice:
    i = db.get(Invoice, iid)
    if i is None:
        raise NotFoundError("Invoice not found")
    return _own(user, i)


@router.get("/{iid}")
def detail(iid: int, user: User = _read, db: Session = Depends(get_session)) -> dict:
    return _out(_get(db, user, iid))


@router.get("/{iid}/pdf")
def pdf(iid: int, user: User = _read, db: Session = Depends(get_session)) -> Response:
    i = _get(db, user, iid)
    return Response(
        render_pdf(i),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{i.number.replace("/", "-")}.pdf"'},
    )

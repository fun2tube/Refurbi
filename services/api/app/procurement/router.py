from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import require_permission
from app.auth.models import User
from app.catalog.models import ProductVariant
from app.core.db import get_session
from app.core.errors import AppError, ConflictError, NotFoundError
from app.core.pagination import Page, PageDep, make_page, paginate
from app.inventory import imei as imei_mod
from app.inventory.lifecycle import transition
from app.inventory.models import Device, DeviceStatus, StockMovement
from app.procurement.ceir import ImeiChecker, get_imei_checker
from app.procurement.models import (
    GoodsReceipt,
    GoodsReceiptItem,
    ImeiCheck,
    ImeiResult,
    POStatus,
    PurchaseOrder,
    PurchaseOrderLine,
    Supplier,
)

router = APIRouter(prefix="/admin/procurement", tags=["procurement-admin"])
_perm = Depends(require_permission("procurement.write"))


class SupplierIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    contact_name: str = ""
    phone: str = ""
    city: str = ""
    notes: str = ""
    is_active: bool = True


class SupplierOut(SupplierIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_demo: bool = False


class LineIn(BaseModel):
    variant_id: int
    quantity: int = Field(gt=0, le=10000)
    unit_cost_paise: int = Field(ge=0)


class POIn(BaseModel):
    supplier_id: int
    notes: str = ""
    lines: list[LineIn] = Field(min_length=1)


class LineOut(LineIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    received: int = 0


class POOut(BaseModel):
    id: int
    supplier_id: int
    supplier_name: str
    status: str
    notes: str
    created_at: datetime
    total_paise: int
    lines: list[LineOut]


class ReceiveItem(BaseModel):
    line_id: int
    imei: str


class ReceiveIn(BaseModel):
    items: list[ReceiveItem] = Field(min_length=1)


class ReceivedDevice(BaseModel):
    device_id: int
    imei_last4: str
    imei_check: str
    status: str


class ReceiptOut(BaseModel):
    receipt_id: int
    po_status: str
    devices: list[ReceivedDevice]


def _commit(db: Session, what: str) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError(f"{what} conflicts with an existing record") from None


# ------------------------------ suppliers ------------------------------
@router.get("/suppliers", response_model=Page[SupplierOut])
def list_suppliers(params: PageDep, db: Session = Depends(get_session), _: User = _perm):
    rows, total = paginate(db, select(Supplier).order_by(Supplier.name), params)
    return make_page([SupplierOut.model_validate(r) for r in rows], total, params)


@router.post("/suppliers", response_model=SupplierOut, status_code=201)
def create_supplier(body: SupplierIn, db: Session = Depends(get_session), _: User = _perm):
    obj = Supplier(**body.model_dump())
    db.add(obj)
    _commit(db, "Supplier")
    return obj


@router.put("/suppliers/{sid}", response_model=SupplierOut)
def update_supplier(
    sid: int, body: SupplierIn, db: Session = Depends(get_session), _: User = _perm
):
    obj = db.get(Supplier, sid)
    if obj is None:
        raise NotFoundError("Supplier not found")
    for k, v in body.model_dump().items():
        setattr(obj, k, v)
    _commit(db, "Supplier")
    return obj


# ------------------------------ purchase orders ------------------------------
def _received_counts(db: Session, po_id: int) -> dict[int, int]:
    rows = db.execute(
        select(GoodsReceiptItem.line_id, func.count())
        .join(GoodsReceipt)
        .where(GoodsReceipt.po_id == po_id)
        .group_by(GoodsReceiptItem.line_id)
    )
    return {line_id: n for line_id, n in rows}


def _po_out(db: Session, po: PurchaseOrder) -> POOut:
    got = _received_counts(db, po.id)
    lines = [
        LineOut(
            id=ln.id,
            variant_id=ln.variant_id,
            quantity=ln.quantity,
            unit_cost_paise=ln.unit_cost_paise,
            received=got.get(ln.id, 0),
        )
        for ln in po.lines
    ]
    return POOut(
        id=po.id,
        supplier_id=po.supplier_id,
        supplier_name=po.supplier.name,
        status=po.status,
        notes=po.notes,
        created_at=po.created_at,
        total_paise=sum(ln.quantity * ln.unit_cost_paise for ln in po.lines),
        lines=lines,
    )


def _get_po(db: Session, po_id: int, *, lock: bool = False) -> PurchaseOrder:
    stmt = (
        select(PurchaseOrder)
        .where(PurchaseOrder.id == po_id)
        .options(selectinload(PurchaseOrder.lines), selectinload(PurchaseOrder.supplier))
    )
    if lock:
        stmt = stmt.with_for_update(of=PurchaseOrder)
    po = db.scalar(stmt)
    if po is None:
        raise NotFoundError("Purchase order not found")
    return po


@router.get("/purchase-orders", response_model=Page[POOut])
def list_pos(
    params: PageDep, status: str | None = None, db: Session = Depends(get_session), _: User = _perm
):
    stmt = (
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.lines), selectinload(PurchaseOrder.supplier))
        .order_by(PurchaseOrder.id.desc())
    )
    if status:
        stmt = stmt.where(PurchaseOrder.status == status)
    rows, total = paginate(db, stmt, params)
    return make_page([_po_out(db, r) for r in rows], total, params)


@router.post("/purchase-orders", response_model=POOut, status_code=201)
def create_po(body: POIn, db: Session = Depends(get_session), user: User = _perm):
    if db.get(Supplier, body.supplier_id) is None:
        raise NotFoundError("Supplier not found")
    for ln in body.lines:
        if db.get(ProductVariant, ln.variant_id) is None:
            raise NotFoundError(f"Variant {ln.variant_id} not found")
    po = PurchaseOrder(supplier_id=body.supplier_id, notes=body.notes, created_by=user.id)
    po.lines = [PurchaseOrderLine(**ln.model_dump()) for ln in body.lines]
    db.add(po)
    db.commit()
    return _po_out(db, _get_po(db, po.id))


@router.get("/purchase-orders/{po_id}", response_model=POOut)
def get_po(po_id: int, db: Session = Depends(get_session), _: User = _perm):
    return _po_out(db, _get_po(db, po_id))


def _set_status(db: Session, po_id: int, allowed_from: set[str], to: POStatus) -> POOut:
    po = _get_po(db, po_id, lock=True)
    if po.status not in allowed_from:
        raise ConflictError(f"Cannot move a purchase order from {po.status} to {to.value}")
    po.status = to.value
    db.commit()
    return _po_out(db, po)


@router.post("/purchase-orders/{po_id}/order", response_model=POOut)
def order_po(po_id: int, db: Session = Depends(get_session), _: User = _perm):
    return _set_status(db, po_id, {POStatus.DRAFT.value}, POStatus.ORDERED)


@router.post("/purchase-orders/{po_id}/cancel", response_model=POOut)
def cancel_po(po_id: int, db: Session = Depends(get_session), _: User = _perm):
    return _set_status(
        db, po_id, {POStatus.DRAFT.value, POStatus.ORDERED.value}, POStatus.CANCELLED
    )


# ------------------------------ goods receipt ------------------------------
@router.post("/purchase-orders/{po_id}/receive", response_model=ReceiptOut, status_code=201)
def receive(
    po_id: int,
    body: ReceiveIn,
    db: Session = Depends(get_session),
    user: User = _perm,
    checker: ImeiChecker = Depends(get_imei_checker),
):
    """Receive devices against a PO. Every unit needs a valid, unique IMEI and gets an IMEI-check
    record; clear units go to IMEI_CHECKED, blocked ones to BLACKLISTED (via the lifecycle)."""
    po = _get_po(db, po_id, lock=True)
    if po.status not in (POStatus.ORDERED.value, POStatus.PARTIALLY_RECEIVED.value):
        raise ConflictError(f"Cannot receive against a {po.status} purchase order")
    lines = {ln.id: ln for ln in po.lines}
    got = _received_counts(db, po.id)
    seen: set[str] = set()
    prepared: list[tuple[ReceiveItem, str]] = []
    for it in body.items:
        if it.line_id not in lines:
            raise NotFoundError(f"Line {it.line_id} is not on this purchase order")
        try:
            n = imei_mod.normalise_imei(it.imei)
        except ValueError as e:
            raise AppError(f"Invalid IMEI: {e}", code="invalid_imei") from None
        if n in seen:
            raise ConflictError("Duplicate IMEI in the same receipt", details={"line": it.line_id})
        seen.add(n)
        prepared.append((it, n))
    pending: dict[int, int] = {}
    for it, _n in prepared:
        pending[it.line_id] = pending.get(it.line_id, 0) + 1
    for lid, extra in pending.items():
        if got.get(lid, 0) + extra > lines[lid].quantity:
            raise ConflictError(f"Receiving more than ordered on line {lid}")
    for _it, n in prepared:
        if db.scalar(select(Device.id).where(Device.imei_hash == imei_mod.hash_imei(n))):
            raise ConflictError("A device with this IMEI already exists")

    receipt = GoodsReceipt(po_id=po.id, received_by=user.id)
    db.add(receipt)
    db.flush()
    out: list[ReceivedDevice] = []
    for it, n in prepared:
        ln = lines[it.line_id]
        dev = Device(
            variant_id=ln.variant_id,
            imei_encrypted=imei_mod.encrypt_imei(n),
            imei_hash=imei_mod.hash_imei(n),
            imei_last4=n[-4:],
            cost_paise=ln.unit_cost_paise,
            status=DeviceStatus.PURCHASED.value,
        )
        db.add(dev)
        db.flush()
        db.add(
            StockMovement(
                device_id=dev.id,
                from_status=None,
                to_status=DeviceStatus.PURCHASED.value,
                to_location="WAREHOUSE",
                reason=f"Goods receipt #{receipt.id} (PO #{po.id})",
                actor_user_id=user.id,
            )
        )
        db.add(GoodsReceiptItem(receipt_id=receipt.id, line_id=ln.id, device_id=dev.id))
        result = checker.check(n)
        db.add(
            ImeiCheck(
                device_id=dev.id, result=result.value, provider=checker.name, checked_by=user.id
            )
        )
        if result == ImeiResult.CLEAR:
            transition(db, dev.id, DeviceStatus.IMEI_CHECKED, actor_user_id=user.id,
                       reason="IMEI check clear")  # fmt: skip
        else:
            transition(db, dev.id, DeviceStatus.BLACKLISTED, actor_user_id=user.id,
                       reason="IMEI check blocked")  # fmt: skip
        db.refresh(dev)
        out.append(
            ReceivedDevice(
                device_id=dev.id,
                imei_last4=dev.imei_last4,
                imei_check=result.value,
                status=dev.status,
            )
        )
    got = _received_counts(db, po.id)
    full = all(got.get(ln.id, 0) >= ln.quantity for ln in po.lines)
    po.status = (POStatus.RECEIVED if full else POStatus.PARTIALLY_RECEIVED).value
    _commit(db, "Goods receipt")
    return ReceiptOut(receipt_id=receipt.id, po_status=po.status, devices=out)

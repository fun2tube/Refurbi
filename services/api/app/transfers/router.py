"""Stock transfer workflow (T15). IMEI is never returned, only last 4 digits."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import current_user, has_permission, require_permission
from app.auth.models import User
from app.core.db import get_session
from app.core.errors import AppError, ConflictError, ForbiddenError, NotFoundError
from app.counters.models import Counter
from app.inventory.lifecycle import Location, transition
from app.inventory.models import Device, DeviceStatus, LocationKind
from app.transfers.models import StockTransfer, StockTransferItem, TransferStatus

router = APIRouter(prefix="/admin/transfers", tags=["transfers"])
_manage = Depends(require_permission("transfers.manage"))
T = TransferStatus


class TransferIn(BaseModel):
    from_counter_id: int | None = None  # null = warehouse
    to_counter_id: int | None = None  # null = warehouse
    device_ids: list[int] = Field(min_length=1, max_length=200)
    note: str = Field(default="", max_length=500)


class ReceiveIn(BaseModel):
    device_ids: list[int] | None = None  # default: everything still in transit


def _out(db: Session, t: StockTransfer) -> dict:
    rows = db.execute(
        select(StockTransferItem, Device)
        .join(Device, Device.id == StockTransferItem.device_id)
        .where(StockTransferItem.transfer_id == t.id)
        .order_by(StockTransferItem.id)
    ).all()
    return {
        "id": t.id,
        "status": t.status,
        "from_counter_id": t.from_counter_id,
        "to_counter_id": t.to_counter_id,
        "note": t.note,
        "created_at": t.created_at,
        "approved_at": t.approved_at,
        "received_at": t.received_at,
        "items": [
            {"device_id": d.id, "imei_last4": d.imei_last4, "received": bool(i.received)}
            for i, d in rows
        ],
    }


def _get(db: Session, tid: int) -> StockTransfer:
    t = db.scalar(select(StockTransfer).where(StockTransfer.id == tid).with_for_update())
    if t is None:
        raise NotFoundError("Transfer not found")
    return t


def _check_counter(db: Session, cid: int | None) -> None:
    if cid is not None:
        c = db.get(Counter, cid)
        if c is None or not c.is_active:
            raise AppError("Counter not found or inactive", code="invalid_counter")


@router.post("", status_code=201)
def create(body: TransferIn, user: User = _manage, db: Session = Depends(get_session)) -> dict:
    if (body.from_counter_id is None) == (body.to_counter_id is None):
        raise AppError("Exactly one side of a transfer must be the warehouse", code="invalid_route")
    _check_counter(db, body.from_counter_id)
    _check_counter(db, body.to_counter_id)
    ids = list(dict.fromkeys(body.device_ids))
    src_kind = LocationKind.WAREHOUSE if body.from_counter_id is None else LocationKind.COUNTER
    for did in ids:
        d = db.get(Device, did)
        if d is None:
            raise NotFoundError(f"Device {did} not found")
        if (
            d.status != DeviceStatus.AVAILABLE.value
            or d.location_kind != src_kind.value
            or d.counter_id != body.from_counter_id
        ):
            raise ConflictError(
                f"Device {did} is not AVAILABLE at the source location", code="device_not_movable"
            )
        busy = db.scalar(
            select(StockTransferItem.id)
            .join(StockTransfer, StockTransfer.id == StockTransferItem.transfer_id)
            .where(StockTransferItem.device_id == did, StockTransfer.status == T.REQUESTED.value)
        )
        if busy:
            raise ConflictError(
                f"Device {did} is already in a pending transfer", code="device_not_movable"
            )
    t = StockTransfer(
        from_counter_id=body.from_counter_id,
        to_counter_id=body.to_counter_id,
        note=body.note,
        requested_by=user.id,
    )
    db.add(t)
    db.flush()
    db.add_all(StockTransferItem(transfer_id=t.id, device_id=i) for i in ids)
    db.commit()
    return _out(db, t)


@router.get("")
def list_transfers(
    status: str | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
) -> list[dict]:
    if not (
        has_permission(user, "transfers.manage")
        or any(
            ur.counter_id and has_permission(user, "transfers.receive", ur.counter_id)
            for ur in user.roles
        )
    ):
        raise ForbiddenError("You do not have permission to do this")
    q = select(StockTransfer).order_by(StockTransfer.id.desc()).limit(200)
    if status:
        q = q.where(StockTransfer.status == status)
    if not has_permission(user, "transfers.manage"):
        mine = [ur.counter_id for ur in user.roles if ur.counter_id]
        q = q.where(StockTransfer.to_counter_id.in_(mine) | StockTransfer.from_counter_id.in_(mine))
    return [_out(db, t) for t in db.scalars(q)]


@router.get("/{tid}")
def detail(tid: int, user: User = _manage, db: Session = Depends(get_session)) -> dict:
    t = db.get(StockTransfer, tid)
    if t is None:
        raise NotFoundError("Transfer not found")
    return _out(db, t)


def _items(db: Session, tid: int) -> list[StockTransferItem]:
    return list(db.scalars(select(StockTransferItem).where(StockTransferItem.transfer_id == tid)))


@router.post("/{tid}/approve")
def approve(tid: int, user: User = _manage, db: Session = Depends(get_session)) -> dict:
    t = _get(db, tid)
    if t.status != T.REQUESTED.value:
        raise ConflictError("Only a REQUESTED transfer can be approved", code="bad_transfer_state")
    for it in _items(db, tid):
        transition(db, it.device_id, DeviceStatus.IN_TRANSIT, actor_user_id=user.id,
                   reason=f"transfer #{t.id}")  # fmt: skip
    t.status, t.approved_by, t.approved_at = T.IN_TRANSIT.value, user.id, datetime.now(UTC)
    db.commit()
    return _out(db, t)


def _end(tid: int, to: T, user: User, db: Session) -> dict:
    t = _get(db, tid)
    if t.status != T.REQUESTED.value:
        raise ConflictError("Only a REQUESTED transfer can be changed", code="bad_transfer_state")
    t.status = to.value
    db.commit()
    return _out(db, t)


@router.post("/{tid}/reject")
def reject(tid: int, user: User = _manage, db: Session = Depends(get_session)) -> dict:
    return _end(tid, T.REJECTED, user, db)


@router.post("/{tid}/cancel")
def cancel(tid: int, user: User = _manage, db: Session = Depends(get_session)) -> dict:
    return _end(tid, T.CANCELLED, user, db)


@router.post("/{tid}/receive")
def receive(
    tid: int,
    body: ReceiveIn | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_session),
) -> dict:
    t = _get(db, tid)
    if not (
        has_permission(user, "transfers.manage")
        or (t.to_counter_id and has_permission(user, "transfers.receive", t.to_counter_id))
    ):
        raise ForbiddenError("You do not have permission to receive this transfer")
    if t.status != T.IN_TRANSIT.value:
        raise ConflictError("Transfer is not in transit", code="bad_transfer_state")
    items = _items(db, tid)
    pending = {i.device_id: i for i in items if not i.received}
    want = body.device_ids if body and body.device_ids else list(pending)
    for did in want:
        if did not in pending:
            raise ConflictError(f"Device {did} is not awaiting receipt", code="bad_transfer_state")
    loc = (
        Location(LocationKind.WAREHOUSE)
        if t.to_counter_id is None
        else Location(LocationKind.COUNTER, t.to_counter_id)
    )
    for did in want:
        transition(db, did, DeviceStatus.AVAILABLE, actor_user_id=user.id,
                   reason=f"transfer #{t.id} received", location=loc)  # fmt: skip
        pending[did].received = 1
    if all(i.received for i in items):
        t.status, t.received_by, t.received_at = T.RECEIVED.value, user.id, datetime.now(UTC)
    db.commit()
    return _out(db, t)

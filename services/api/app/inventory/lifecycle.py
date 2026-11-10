"""Device lifecycle state machine (D7). The ONLY place that may change `Device.status`.

Every transition is validated against ALLOWED, checked against guards, and writes a
stock_movements row plus an audit_log row in the caller's transaction (flush, no commit: the
caller commits, so a failed transition leaves no trace). Rows are locked (SELECT ... FOR UPDATE)
to serialise concurrent transitions on Postgres.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, ConflictError, NotFoundError
from app.inventory.models import (
    AuditLog,
    Device,
    DeviceStatus,
    DeviceTest,
    LocationKind,
    StockMovement,
)

S = DeviceStatus

ALLOWED: dict[S, frozenset[S]] = {
    S.PURCHASED: frozenset({S.IMEI_CHECKED, S.BLACKLISTED, S.WRITTEN_OFF}),
    S.IMEI_CHECKED: frozenset({S.QC_PENDING, S.BLACKLISTED, S.WRITTEN_OFF}),
    S.QC_PENDING: frozenset({S.QC_PASSED, S.QC_FAILED}),
    S.QC_PASSED: frozenset({S.AVAILABLE, S.QC_PENDING}),
    S.QC_FAILED: frozenset({S.REPAIR, S.QC_PENDING, S.WRITTEN_OFF}),
    S.REPAIR: frozenset({S.QC_PENDING, S.WRITTEN_OFF}),
    S.AVAILABLE: frozenset({S.RESERVED, S.IN_TRANSIT, S.SOLD, S.QC_PENDING, S.WRITTEN_OFF}),
    S.RESERVED: frozenset({S.AVAILABLE, S.SOLD}),
    S.IN_TRANSIT: frozenset({S.AVAILABLE}),
    S.SOLD: frozenset({S.RETURNED, S.WARRANTY_HOLD}),
    S.RETURNED: frozenset({S.QC_PENDING, S.WRITTEN_OFF}),
    S.WARRANTY_HOLD: frozenset({S.REPAIR, S.RETURNED, S.SOLD, S.WRITTEN_OFF}),
    S.BLACKLISTED: frozenset({S.WRITTEN_OFF}),
    S.WRITTEN_OFF: frozenset(),
}

# Transitions that must carry a human reason.
REASON_REQUIRED = frozenset(
    {S.QC_FAILED, S.BLACKLISTED, S.WRITTEN_OFF, S.RETURNED, S.WARRANTY_HOLD}
)


class InvalidTransitionError(ConflictError):
    code = "invalid_transition"


class GuardFailedError(ConflictError):
    code = "transition_guard_failed"


@dataclass(frozen=True)
class Location:
    kind: LocationKind
    counter_id: int | None = None

    def __post_init__(self) -> None:
        if (self.kind == LocationKind.COUNTER) != (self.counter_id is not None):
            raise ValueError("counter_id is required for, and only for, COUNTER locations")


def _loc_str(kind: str, counter_id: int | None) -> str:
    return f"{kind}:{counter_id}" if counter_id is not None else kind


def _snapshot(d: Device) -> dict:
    return {
        "status": d.status,
        "location_kind": d.location_kind,
        "counter_id": d.counter_id,
        "grade": d.grade,
        "price_paise": d.price_paise,
    }


def _has_current_test(db: Session, device_id: int, passed: bool) -> bool:
    return (
        db.scalar(
            select(DeviceTest.id).where(
                DeviceTest.device_id == device_id,
                DeviceTest.is_current.is_(True),
                DeviceTest.passed.is_(passed),
            )
        )
        is not None
    )


def _imei_check_recorded(db: Session, device_id: int) -> bool:
    return (
        db.scalar(
            select(StockMovement.id).where(
                StockMovement.device_id == device_id,
                StockMovement.to_status == S.IMEI_CHECKED.value,
            )
        )
        is not None
    )


def _check_guards(db: Session, d: Device, frm: S, to: S, location: Location | None) -> None:
    if to == S.QC_PASSED and not _has_current_test(db, d.id, True):
        raise GuardFailedError("QC cannot pass without a current passing QC test")
    if to == S.QC_FAILED and not _has_current_test(db, d.id, False):
        raise GuardFailedError("QC cannot fail without a current failing QC test")
    if frm == S.QC_PASSED and to == S.AVAILABLE:
        if not _imei_check_recorded(db, d.id):
            raise GuardFailedError("Device cannot become AVAILABLE without a recorded IMEI check")
        if d.grade is None or d.price_paise is None:
            raise GuardFailedError("Device needs a grade and a price before it can be AVAILABLE")
    if frm == S.IN_TRANSIT and to == S.AVAILABLE:
        if location is None or location.kind == LocationKind.IN_TRANSIT:
            raise GuardFailedError("Receiving an in-transit device needs a destination location")
    elif location is not None and to != S.IN_TRANSIT:
        raise GuardFailedError("A location may only be set when sending or receiving a transfer")


def transition(
    db: Session,
    device_id: int,
    to: S | str,
    *,
    actor_user_id: int | None = None,
    reason: str = "",
    location: Location | None = None,
) -> Device:
    """Move a device to a new status. Raises InvalidTransitionError / GuardFailedError."""
    try:
        to = S(to)
    except ValueError:
        raise AppError(f"Unknown device status: {to}", code="unknown_status") from None
    d = db.scalar(select(Device).where(Device.id == device_id).with_for_update())
    if d is None:
        raise NotFoundError("Device not found")
    frm = S(d.status)
    if to not in ALLOWED[frm]:
        raise InvalidTransitionError(
            f"Cannot move a device from {frm.value} to {to.value}",
            details={
                "from": frm.value,
                "to": to.value,
                "allowed": sorted(s.value for s in ALLOWED[frm]),
            },
        )
    reason = reason.strip()
    if to in REASON_REQUIRED and not reason:
        raise GuardFailedError(f"A reason is required to move a device to {to.value}")
    _check_guards(db, d, frm, to, location)

    before = _snapshot(d)
    from_loc = _loc_str(d.location_kind, d.counter_id)
    if to == S.IN_TRANSIT:
        d.location_kind, d.counter_id = LocationKind.IN_TRANSIT.value, None
    elif frm == S.IN_TRANSIT and location is not None:
        d.location_kind, d.counter_id = location.kind.value, location.counter_id
    d.status = to.value
    db.add(
        StockMovement(
            device_id=d.id,
            from_status=frm.value,
            to_status=to.value,
            from_location=from_loc,
            to_location=_loc_str(d.location_kind, d.counter_id),
            reason=reason[:255],
            actor_user_id=actor_user_id,
        )
    )
    db.add(
        AuditLog(
            entity_type="device",
            entity_id=d.id,
            action=f"status:{frm.value}->{to.value}",
            actor_user_id=actor_user_id,
            before=before,
            after=_snapshot(d),
        )
    )
    db.flush()
    return d

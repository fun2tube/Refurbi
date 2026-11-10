from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.deps import require_permission
from app.auth.models import User
from app.core.db import get_session
from app.core.errors import AppError, NotFoundError
from app.inventory.models import AuditLog, Device
from app.pricing import service as svc
from app.pricing.models import DeviceCost, PricingRule

router = APIRouter(prefix="/admin/pricing", tags=["pricing-admin"])
_perm = Depends(require_permission("pricing.write"))


class RuleIn(BaseModel):
    target_margin_bps: int = Field(ge=0, le=10000)


class CostIn(BaseModel):
    kind: Literal["REPAIR", "LOGISTICS"]
    amount_paise: int = Field(gt=0)
    note: str = Field(default="", max_length=255)


class PriceIn(BaseModel):
    price_paise: int = Field(ge=0)
    reason: str = Field(min_length=3, max_length=255)
    allow_below_cost: bool = False


def _rules(db: Session) -> dict[str, int]:
    out = dict(svc.DEFAULT_MARGIN_BPS)
    out.update({r.grade: r.target_margin_bps for r in db.scalars(select(PricingRule))})
    return out


def _dev(db: Session, device_id: int) -> Device:
    d = db.get(Device, device_id)
    if d is None:
        raise NotFoundError("Device not found")
    return d


def _breakdown(db: Session, d: Device) -> dict:
    sums = dict(
        db.execute(
            select(DeviceCost.kind, func.sum(DeviceCost.amount_paise))
            .where(DeviceCost.device_id == d.id)
            .group_by(DeviceCost.kind)
        ).all()
    )
    repair, logistics = int(sums.get("REPAIR", 0)), int(sums.get("LOGISTICS", 0))
    landed = svc.landed_cost(d.cost_paise, repair, logistics)
    bps = _rules(db).get(d.grade) if d.grade else None
    return {
        "device_id": d.id,
        "grade": d.grade,
        "purchase_paise": d.cost_paise,
        "repair_paise": repair,
        "logistics_paise": logistics,
        "landed_cost_paise": landed,
        "target_margin_bps": bps,
        "suggested_price_paise": svc.suggested_price(landed, bps) if bps is not None else None,
        "price_paise": d.price_paise,
        "margin_bps": svc.margin_bps_at(d.price_paise, landed)
        if d.price_paise is not None
        else None,
    }


@router.get("/rules")
def list_rules(db: Session = Depends(get_session), _: User = _perm):
    return [{"grade": g, "target_margin_bps": b} for g, b in sorted(_rules(db).items())]


@router.put("/rules/{grade}")
def set_rule(grade: str, body: RuleIn, db: Session = Depends(get_session), user: User = _perm):
    if grade not in svc.DEFAULT_MARGIN_BPS:
        raise AppError("Unknown grade", code="unknown_grade")
    r = db.get(PricingRule, grade)
    before = _rules(db)[grade]
    if r is None:
        db.add(
            PricingRule(grade=grade, target_margin_bps=body.target_margin_bps, updated_by=user.id)
        )
    else:
        r.target_margin_bps, r.updated_by = body.target_margin_bps, user.id
    db.commit()
    return {"grade": grade, "target_margin_bps": body.target_margin_bps, "previous": before}


@router.get("/devices/{device_id}")
def device_pricing(device_id: int, db: Session = Depends(get_session), _: User = _perm):
    return _breakdown(db, _dev(device_id=device_id, db=db))


@router.post("/devices/{device_id}/costs", status_code=201)
def add_cost(device_id: int, body: CostIn, db: Session = Depends(get_session), user: User = _perm):
    d = _dev(db, device_id)
    db.add(DeviceCost(device_id=d.id, created_by=user.id, **body.model_dump()))
    db.add(
        AuditLog(
            entity_type="device", entity_id=d.id, action=f"cost:{body.kind}",
            actor_user_id=user.id, after=body.model_dump(),
        )
    )  # fmt: skip
    db.commit()
    return _breakdown(db, d)


def _set_price(db: Session, d: Device, price: int, user: User, action: str, reason: str) -> dict:
    before = d.price_paise
    d.price_paise = price
    db.add(
        AuditLog(
            entity_type="device", entity_id=d.id, action=action, actor_user_id=user.id,
            before={"price_paise": before}, after={"price_paise": price, "reason": reason},
        )
    )  # fmt: skip
    db.commit()
    return _breakdown(db, d)


@router.post("/devices/{device_id}/apply-suggested")
def apply_suggested(device_id: int, db: Session = Depends(get_session), user: User = _perm):
    d = _dev(db, device_id)
    b = _breakdown(db, d)
    if b["suggested_price_paise"] is None:
        raise AppError("Device has no grade yet; finish QC first", code="no_grade")
    return _set_price(db, d, b["suggested_price_paise"], user, "price:suggested", "suggested price")


@router.put("/devices/{device_id}/price")
def override_price(
    device_id: int, body: PriceIn, db: Session = Depends(get_session), user: User = _perm
):
    d = _dev(db, device_id)
    landed = _breakdown(db, d)["landed_cost_paise"]
    if body.price_paise < landed and not body.allow_below_cost:
        raise AppError(
            "Price is below landed cost; set allow_below_cost to confirm",
            code="below_cost",
            details={"landed_cost_paise": landed},
        )
    return _set_price(db, d, body.price_paise, user, "price:override", body.reason)

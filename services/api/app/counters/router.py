from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.deps import require_permission
from app.auth.models import User
from app.catalog.models import ProductModel
from app.core.db import get_session
from app.core.errors import AppError, ConflictError, NotFoundError
from app.counters.models import CommissionRule as Rule
from app.counters.models import Counter, CounterAgreement
from app.inventory.models import AuditLog

router = APIRouter(prefix="/admin/counters", tags=["counters-admin"])
_perm = Depends(require_permission("counters.manage"))


class CounterIn(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,78}$")
    name: str = Field(min_length=1, max_length=120)
    city: str = ""
    address: str = ""
    owner_name: str = ""
    phone: str = ""
    is_active: bool = True


class CounterOut(CounterIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_verified: bool
    is_demo: bool


class AgreementIn(BaseModel):
    start_date: date
    end_date: date | None = None
    document_ref: str = ""
    notes: str = ""

    @model_validator(mode="after")
    def _order(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date")
        return self


class AgreementOut(AgreementIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class RuleIn(BaseModel):
    model_id: int | None = None
    kind: str = Field(pattern="^(FLAT|PERCENT)$")
    value: int = Field(ge=0, description="paise for FLAT, basis points for PERCENT")
    is_active: bool = True

    @model_validator(mode="after")
    def _cap(self):
        if self.kind == "PERCENT" and self.value > 10_000:
            raise ValueError("PERCENT value is in basis points (max 10000)")
        return self


class RuleOut(RuleIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    counter_id: int


def _counter(db: Session, cid: int) -> Counter:
    c = db.get(Counter, cid)
    if c is None:
        raise NotFoundError("Counter not found")
    return c


@router.get("", response_model=list[CounterOut])
def list_counters(db: Session = Depends(get_session), _: User = _perm):
    return db.scalars(select(Counter).order_by(Counter.name)).all()


@router.post("", response_model=CounterOut, status_code=201)
def create_counter(body: CounterIn, db: Session = Depends(get_session), user: User = _perm):
    c = Counter(**body.model_dump())  # always created unverified
    db.add(c)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("A counter with this slug already exists") from None
    return c


@router.put("/{cid}", response_model=CounterOut)
def update_counter(cid: int, body: CounterIn, db: Session = Depends(get_session), _: User = _perm):
    c = _counter(db, cid)
    for k, v in body.model_dump().items():
        setattr(c, k, v)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("A counter with this slug already exists") from None
    return c


@router.post("/{cid}/verify", response_model=CounterOut)
def verify(cid: int, db: Session = Depends(get_session), user: User = _perm):
    """Publishing a counter needs an agreement that is currently in force."""
    c = _counter(db, cid)
    today = date.today()
    ok = db.scalar(
        select(CounterAgreement.id).where(
            CounterAgreement.counter_id == c.id,
            CounterAgreement.start_date <= today,
            (CounterAgreement.end_date.is_(None)) | (CounterAgreement.end_date >= today),
        )
    )
    if ok is None:
        raise AppError("Add an active agreement before verifying", code="no_agreement")
    c.is_verified = True
    db.add(AuditLog(entity_type="counter", entity_id=c.id, action="verified",
                    actor_user_id=user.id))  # fmt: skip
    db.commit()
    return c


@router.post("/{cid}/unverify", response_model=CounterOut)
def unverify(cid: int, db: Session = Depends(get_session), user: User = _perm):
    c = _counter(db, cid)
    c.is_verified = False
    db.add(AuditLog(entity_type="counter", entity_id=c.id, action="unverified",
                    actor_user_id=user.id))  # fmt: skip
    db.commit()
    return c


@router.get("/{cid}/agreements", response_model=list[AgreementOut])
def list_agreements(cid: int, db: Session = Depends(get_session), _: User = _perm):
    _counter(db, cid)
    return db.scalars(
        select(CounterAgreement)
        .where(CounterAgreement.counter_id == cid)
        .order_by(CounterAgreement.start_date.desc())
    ).all()


@router.post("/{cid}/agreements", response_model=AgreementOut, status_code=201)
def add_agreement(cid: int, body: AgreementIn, db: Session = Depends(get_session), _: User = _perm):
    _counter(db, cid)
    a = CounterAgreement(counter_id=cid, **body.model_dump())
    db.add(a)
    db.commit()
    return a


@router.get("/{cid}/commission-rules", response_model=list[RuleOut])
def list_rules(cid: int, db: Session = Depends(get_session), _: User = _perm):
    _counter(db, cid)
    return db.scalars(select(Rule).where(Rule.counter_id == cid).order_by(Rule.id)).all()


@router.post("/{cid}/commission-rules", response_model=RuleOut, status_code=201)
def add_rule(cid: int, body: RuleIn, db: Session = Depends(get_session), user: User = _perm):
    _counter(db, cid)
    if body.model_id is not None and db.get(ProductModel, body.model_id) is None:
        raise NotFoundError("Model not found")
    if (
        db.scalar(
            select(Rule.id).where(
                Rule.counter_id == cid, Rule.model_id == body.model_id, Rule.is_active.is_(True)
            )
        )
        and body.is_active
    ):
        raise ConflictError("An active rule already exists for this counter/model; deactivate it")
    r = Rule(counter_id=cid, **body.model_dump())
    db.add(r)
    db.flush()
    db.add(AuditLog(entity_type="commission_rule", entity_id=r.id, action="created",
                    actor_user_id=user.id, after=body.model_dump()))  # fmt: skip
    db.commit()
    return r


@router.post("/{cid}/commission-rules/{rid}/deactivate", response_model=RuleOut)
def deactivate_rule(cid: int, rid: int, db: Session = Depends(get_session), user: User = _perm):
    r = db.get(Rule, rid)
    if r is None or r.counter_id != cid:
        raise NotFoundError("Rule not found")
    r.is_active = False
    db.add(AuditLog(entity_type="commission_rule", entity_id=r.id, action="deactivated",
                    actor_user_id=user.id))  # fmt: skip
    db.commit()
    return r

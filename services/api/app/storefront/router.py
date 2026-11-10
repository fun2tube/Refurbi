"""Public, read-only storefront API (founder-approved storefront-first priority).

Hard rule: responses are whitelist schemas. They never contain IMEI, purchase cost, supplier,
commission or customer data. Only AVAILABLE devices with a price are listed.
"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.catalog.models import Brand, ProductModel, ProductVariant
from app.catalog.schemas import BrandOut
from app.core.db import get_session
from app.core.errors import NotFoundError
from app.core.pagination import Page, PageDep, make_page
from app.counters.models import Counter
from app.inventory.models import Device, DeviceStatus, LocationKind

router = APIRouter(prefix="/public", tags=["storefront"])


class StoreRef(BaseModel):
    slug: str
    name: str
    city: str


class UnitModelRef(BaseModel):
    slug: str
    name: str
    brand: BrandOut
    is_5g: bool


class UnitOut(BaseModel):
    unit_id: int
    model: UnitModelRef
    storage_gb: int
    ram_gb: int | None
    color: str | None
    grade: str | None
    battery_health: int | None
    price_paise: int
    store: StoreRef | None  # None = ships from the Refurbi warehouse
    photos: list[str]


class ModelStock(BaseModel):
    slug: str
    name: str
    brand: BrandOut
    release_year: int | None
    is_5g: bool
    units_available: int
    from_price_paise: int


class StoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    slug: str
    name: str
    city: str
    is_demo: bool
    units_available: int = 0


def _available():
    return (
        Device.status == DeviceStatus.AVAILABLE.value,
        Device.price_paise.is_not(None),
        ProductVariant.is_active,
        ProductModel.is_active,
        Brand.is_active,
    )


def _base_select(*cols):
    return (
        select(*cols)
        .select_from(Device)
        .join(ProductVariant, Device.variant_id == ProductVariant.id)
        .join(ProductModel, ProductVariant.model_id == ProductModel.id)
        .join(Brand, ProductModel.brand_id == Brand.id)
        .where(*_available())
    )


def _unit(d: Device, v: ProductVariant, m: ProductModel, b: Brand, c: Counter | None) -> UnitOut:
    assert d.price_paise is not None
    return UnitOut(
        unit_id=d.id,
        model=UnitModelRef(
            slug=m.slug, name=m.name, brand=BrandOut(slug=b.slug, name=b.name), is_5g=m.is_5g
        ),
        storage_gb=v.storage_gb,
        ram_gb=v.ram_gb,
        color=v.color,
        grade=d.grade,
        battery_health=d.battery_health,
        price_paise=d.price_paise,
        store=StoreRef(slug=c.slug, name=c.name, city=c.city) if c else None,
        photos=[p.url for p in d.photos if p.url.startswith(("https://", "/"))],
    )


SortKey = Literal["price_asc", "price_desc", "newest", "battery"]


@router.get("/units", response_model=Page[UnitOut])
def list_units(
    params: PageDep,
    db: Session = Depends(get_session),
    brand: str | None = None,
    model: str | None = None,
    q: Annotated[str | None, Query(max_length=60)] = None,
    min_price: Annotated[int | None, Query(ge=0, description="paise")] = None,
    max_price: Annotated[int | None, Query(ge=0, description="paise")] = None,
    storage: Annotated[int | None, Query(gt=0)] = None,
    ram: Annotated[int | None, Query(gt=0)] = None,
    grade: Annotated[str | None, Query(pattern="^[ABC]$")] = None,
    min_battery: Annotated[int | None, Query(ge=0, le=100)] = None,
    is_5g: bool | None = None,
    store: str | None = None,
    sort: SortKey = "newest",
):
    stmt = _base_select(Device, ProductVariant, ProductModel, Brand, Counter).outerjoin(
        Counter, Device.counter_id == Counter.id
    )
    if brand:
        stmt = stmt.where(Brand.slug == brand)
    if model:
        stmt = stmt.where(ProductModel.slug == model)
    if q and q.strip():
        like = f"%{q.strip().lower().replace('%', '').replace('_', '')}%"
        stmt = stmt.where(
            func.lower(ProductModel.name).like(like) | func.lower(Brand.name).like(like)
        )
    if min_price is not None:
        stmt = stmt.where(Device.price_paise >= min_price)
    if max_price is not None:
        stmt = stmt.where(Device.price_paise <= max_price)
    if storage:
        stmt = stmt.where(ProductVariant.storage_gb == storage)
    if ram:
        stmt = stmt.where(ProductVariant.ram_gb == ram)
    if grade:
        stmt = stmt.where(Device.grade == grade)
    if min_battery is not None:
        stmt = stmt.where(Device.battery_health >= min_battery)
    if is_5g is not None:
        stmt = stmt.where(ProductModel.is_5g == is_5g)
    if store:
        stmt = stmt.where(Counter.slug == store)
    order = {
        "price_asc": (Device.price_paise.asc(), Device.id),
        "price_desc": (Device.price_paise.desc(), Device.id),
        "battery": (Device.battery_health.desc().nulls_last(), Device.id),
        "newest": (Device.id.desc(),),
    }[sort]
    stmt = stmt.order_by(*order)
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.execute(stmt.limit(params.page_size).offset(params.offset)).all()
    return make_page([_unit(*r) for r in rows], total, params)


@router.get("/units/{unit_id}", response_model=UnitOut)
def get_unit(unit_id: int, db: Session = Depends(get_session)):
    stmt = (
        _base_select(Device, ProductVariant, ProductModel, Brand, Counter)
        .outerjoin(Counter, Device.counter_id == Counter.id)
        .where(Device.id == unit_id)
    )
    row = db.execute(stmt).first()
    if row is None:
        raise NotFoundError("Unit not found")
    return _unit(*row)


@router.get("/models", response_model=list[ModelStock])
def models_in_stock(
    db: Session = Depends(get_session),
    brand: str | None = None,
    max_price: Annotated[int | None, Query(ge=0)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 60,
):
    stmt = (
        _base_select(
            ProductModel,
            Brand,
            func.count(Device.id).label("n"),
            func.min(Device.price_paise).label("lo"),
        )
        .group_by(ProductModel.id, Brand.id)
        .order_by(func.count(Device.id).desc(), ProductModel.name)
        .limit(limit)
    )
    if brand:
        stmt = stmt.where(Brand.slug == brand)
    if max_price is not None:
        stmt = stmt.where(Device.price_paise <= max_price)
    return [
        ModelStock(
            slug=m.slug,
            name=m.name,
            brand=BrandOut(slug=b.slug, name=b.name),
            release_year=m.release_year,
            is_5g=m.is_5g,
            units_available=n,
            from_price_paise=lo,
        )
        for m, b, n, lo in db.execute(stmt).all()
    ]


@router.get("/brands", response_model=list[BrandOut])
def brands_in_stock(db: Session = Depends(get_session)):
    stmt = _base_select(Brand).distinct().order_by(Brand.name)
    return [BrandOut(slug=b.slug, name=b.name) for (b,) in db.execute(stmt).all()]


def _store_counts(db: Session) -> dict[int, int]:
    stmt = _base_select(Device.counter_id, func.count(Device.id)).where(
        Device.location_kind == LocationKind.COUNTER.value
    )
    return dict(db.execute(stmt.group_by(Device.counter_id)).all())


@router.get("/stores", response_model=list[StoreOut])
def list_stores(db: Session = Depends(get_session)):
    counts = _store_counts(db)
    counters = db.scalars(select(Counter).order_by(Counter.name)).all()
    return [
        StoreOut(
            slug=c.slug,
            name=c.name,
            city=c.city,
            is_demo=c.is_demo,
            units_available=counts.get(c.id, 0),
        )
        for c in counters
    ]


@router.get("/stores/{slug}", response_model=StoreOut)
def get_store(slug: str, db: Session = Depends(get_session)):
    c = db.scalar(select(Counter).where(Counter.slug == slug))
    if c is None:
        raise NotFoundError("Store not found")
    return StoreOut(
        slug=c.slug,
        name=c.name,
        city=c.city,
        is_demo=c.is_demo,
        units_available=_store_counts(db).get(c.id, 0),
    )

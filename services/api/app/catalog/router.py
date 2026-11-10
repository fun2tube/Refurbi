from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import require_permission
from app.catalog import schemas as s
from app.catalog.models import Brand, ProductImage, ProductModel, ProductVariant, Specification
from app.core.db import get_session
from app.core.errors import ConflictError, NotFoundError
from app.core.pagination import Page, PageDep, make_page, paginate

public = APIRouter(prefix="/catalog", tags=["catalog"])
admin = APIRouter(prefix="/admin/catalog", tags=["catalog-admin"])

_read = Depends(require_permission("catalog.read"))
_write = Depends(require_permission("catalog.write"))


def _commit(db: Session, what: str) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError(f"{what} conflicts with an existing record") from None


def _get(db: Session, model, ident, what: str):
    obj = db.get(model, ident)
    if obj is None:
        raise NotFoundError(f"{what} not found")
    return obj


def _model_by_slug(db: Session, slug: str, *, only_active: bool) -> ProductModel:
    stmt = (
        select(ProductModel)
        .where(ProductModel.slug == slug)
        .options(
            selectinload(ProductModel.variants),
            selectinload(ProductModel.specifications),
            selectinload(ProductModel.images),
        )
    )
    obj = db.scalar(stmt)
    if obj is None or (only_active and not (obj.is_active and obj.brand.is_active)):
        raise NotFoundError("Model not found")
    return obj


# ------------------------------ public ------------------------------
@public.get("/brands", response_model=list[s.BrandOut])
def list_brands(db: Session = Depends(get_session)):
    return db.scalars(select(Brand).where(Brand.is_active).order_by(Brand.name)).all()


@public.get("/models", response_model=Page[s.ModelSummary])
def list_models(params: PageDep, brand: str | None = None, db: Session = Depends(get_session)):
    stmt = (
        select(ProductModel)
        .join(Brand)
        .where(ProductModel.is_active, Brand.is_active)
        .order_by(Brand.name, ProductModel.release_year.desc(), ProductModel.name)
    )
    if brand:
        stmt = stmt.where(Brand.slug == brand)
    rows, total = paginate(db, stmt, params)
    return make_page([s.ModelSummary.model_validate(r) for r in rows], total, params)


@public.get("/models/{slug}", response_model=s.ModelDetail)
def get_model(slug: str, db: Session = Depends(get_session)):
    m = _model_by_slug(db, slug, only_active=True)
    detail = s.ModelDetail.model_validate(m)
    detail.variants = [s.VariantOut.model_validate(v) for v in m.variants if v.is_active]
    return detail


# ------------------------------ admin: brands ------------------------------
@admin.get("/brands", response_model=list[s.BrandAdmin])
def admin_brands(db: Session = Depends(get_session), _=_read):
    return db.scalars(select(Brand).order_by(Brand.name)).all()


@admin.post("/brands", response_model=s.BrandAdmin, status_code=201)
def create_brand(body: s.BrandIn, db: Session = Depends(get_session), _=_write):
    brand = Brand(name=body.name, slug=body.slug or s.slugify(body.name))
    db.add(brand)
    _commit(db, "Brand")
    return brand


@admin.patch("/brands/{brand_id}", response_model=s.BrandAdmin)
def patch_brand(brand_id: int, body: s.BrandPatch, db: Session = Depends(get_session), _=_write):
    brand = _get(db, Brand, brand_id, "Brand")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(brand, k, v)
    _commit(db, "Brand")
    return brand


# ------------------------------ admin: models ------------------------------
@admin.get("/models", response_model=Page[s.ModelSummary])
def admin_models(params: PageDep, db: Session = Depends(get_session), _=_read):
    rows, total = paginate(
        db, select(ProductModel).join(Brand).order_by(Brand.name, ProductModel.name), params
    )
    return make_page([s.ModelSummary.model_validate(r) for r in rows], total, params)


@admin.get("/models/{slug}", response_model=s.ModelAdmin)
def admin_model(slug: str, db: Session = Depends(get_session), _=_read):
    return _model_by_slug(db, slug, only_active=False)


@admin.post("/models", response_model=s.ModelAdmin, status_code=201)
def create_model(body: s.ModelIn, db: Session = Depends(get_session), _=_write):
    brand = _get(db, Brand, body.brand_id, "Brand")
    slug = body.slug or s.model_slug(brand.name, body.name)
    m = ProductModel(**body.model_dump(exclude={"slug"}), slug=slug)
    db.add(m)
    _commit(db, "Model")
    return _model_by_slug(db, slug, only_active=False)


@admin.patch("/models/{slug}", response_model=s.ModelAdmin)
def patch_model(slug: str, body: s.ModelPatch, db: Session = Depends(get_session), _=_write):
    m = _model_by_slug(db, slug, only_active=False)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(m, k, v)
    _commit(db, "Model")
    return m


# ------------------------------ admin: variants ------------------------------
@admin.post("/models/{slug}/variants", response_model=s.VariantAdmin, status_code=201)
def create_variant(slug: str, body: s.VariantIn, db: Session = Depends(get_session), _=_write):
    m = _model_by_slug(db, slug, only_active=False)
    parts = [m.slug, f"{body.storage_gb}gb"]
    if body.ram_gb:
        parts.append(f"{body.ram_gb}gb-ram")
    if body.color:
        parts.append(s.slugify(body.color))
    v = ProductVariant(model_id=m.id, sku="-".join(parts), **body.model_dump())
    db.add(v)
    _commit(db, "Variant")
    return v


@admin.patch("/variants/{variant_id}", response_model=s.VariantAdmin)
def patch_variant(
    variant_id: int, body: s.VariantPatch, db: Session = Depends(get_session), _=_write
):
    v = _get(db, ProductVariant, variant_id, "Variant")
    for k, val in body.model_dump(exclude_unset=True).items():
        setattr(v, k, val)
    _commit(db, "Variant")
    return v


# ------------------------------ admin: specs & images ------------------------------
@admin.put("/models/{slug}/specifications", response_model=list[s.SpecOut])
def replace_specs(slug: str, body: list[s.SpecIn], db: Session = Depends(get_session), _=_write):
    if len({b.key for b in body}) != len(body):
        raise ConflictError("Duplicate specification keys")
    m = _model_by_slug(db, slug, only_active=False)
    m.specifications.clear()
    db.flush()
    m.specifications.extend(
        Specification(key=b.key, value=b.value, sort_order=i) for i, b in enumerate(body)
    )
    _commit(db, "Specifications")
    return m.specifications


@admin.post("/models/{slug}/images", response_model=s.ImageOut, status_code=201)
def add_image(slug: str, body: s.ImageIn, db: Session = Depends(get_session), _=_write):
    m = _model_by_slug(db, slug, only_active=False)
    img = ProductImage(model_id=m.id, **body.model_dump())
    db.add(img)
    _commit(db, "Image")
    return img


@admin.delete("/images/{image_id}", status_code=204)
def delete_image(image_id: int, db: Session = Depends(get_session), _=_write):
    db.delete(_get(db, ProductImage, image_id, "Image"))
    db.commit()
    return Response(status_code=204)

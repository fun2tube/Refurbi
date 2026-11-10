import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=120)]
SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    return SLUG_RE.sub("-", text.lower()).strip("-")


def model_slug(brand_name: str, model_name: str) -> str:
    """Brand-prefixed slug unless the model name already carries the brand (iPhone, OnePlus)."""
    first = slugify(brand_name)
    if first == "apple" or slugify(model_name).startswith(first):
        return slugify(model_name)
    return slugify(f"{brand_name} {model_name}")


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- public (whitelist only; never add cost/IMEI/supplier fields here) ----
class BrandOut(ORM):
    slug: str
    name: str


class VariantOut(ORM):
    sku: str
    storage_gb: int
    ram_gb: int | None
    color: str | None


class SpecOut(ORM):
    key: str
    value: str


class ImageOut(ORM):
    url: str
    alt: str


class ModelSummary(ORM):
    slug: str
    name: str
    brand: BrandOut
    release_year: int | None
    is_5g: bool


class ModelDetail(ModelSummary):
    description: str
    variants: list[VariantOut]
    specifications: list[SpecOut]
    images: list[ImageOut]


# ---- admin ----
class BrandIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: Slug | None = None


class BrandPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None


class BrandAdmin(BrandOut):
    id: int
    is_active: bool


class ModelIn(BaseModel):
    brand_id: int
    name: str = Field(min_length=1, max_length=150)
    slug: Slug | None = None
    release_year: int | None = Field(default=None, ge=2000, le=2100)
    is_5g: bool = False
    description: str = ""


class ModelPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    release_year: int | None = Field(default=None, ge=2000, le=2100)
    is_5g: bool | None = None
    description: str | None = None
    is_active: bool | None = None


class VariantAdmin(VariantOut):
    id: int
    is_active: bool


class ModelAdmin(ModelDetail):
    id: int
    is_active: bool
    variants: list[VariantAdmin]  # type: ignore[assignment]


class VariantIn(BaseModel):
    storage_gb: int = Field(gt=0)
    ram_gb: int | None = Field(default=None, gt=0)
    color: str | None = Field(default=None, max_length=50)


class VariantPatch(BaseModel):
    color: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None


class SpecIn(BaseModel):
    key: str = Field(min_length=1, max_length=80)
    value: str = Field(min_length=1, max_length=255)


class ImageIn(BaseModel):
    url: str = Field(min_length=1, max_length=500, pattern=r"^(https://|/)")
    alt: str = Field(default="", max_length=200)
    sort_order: int = 0

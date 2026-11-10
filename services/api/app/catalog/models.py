"""Catalogue: brand -> product model -> sellable variant. Physical handsets live in T07 (devices).

Nothing here is sensitive: IMEI, cost and supplier data belong to devices/procurement only.
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.auth.models import ID
from app.core.db import Base


class Brand(Base):
    __tablename__ = "brands"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ProductModel(Base):
    __tablename__ = "product_models"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True)
    name: Mapped[str] = mapped_column(String(150))
    release_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_5g: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    brand: Mapped[Brand] = relationship(lazy="joined")
    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="model", order_by="ProductVariant.storage_gb, ProductVariant.ram_gb"
    )
    specifications: Mapped[list["Specification"]] = relationship(
        order_by="Specification.sort_order, Specification.id", cascade="all, delete-orphan"
    )
    images: Mapped[list["ProductImage"]] = relationship(
        order_by="ProductImage.sort_order, ProductImage.id", cascade="all, delete-orphan"
    )


class ProductVariant(Base):
    """A sellable configuration, e.g. iPhone 13 / 128 GB / 4 GB. Colour is optional."""

    __tablename__ = "product_variants"
    __table_args__ = (
        CheckConstraint("storage_gb > 0", name="storage_positive"),
        CheckConstraint("ram_gb IS NULL OR ram_gb > 0", name="ram_positive"),
    )
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("product_models.id"), index=True)
    sku: Mapped[str] = mapped_column(String(160), unique=True)
    storage_gb: Mapped[int] = mapped_column(Integer)
    ram_gb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    model: Mapped[ProductModel] = relationship(back_populates="variants")


class Specification(Base):
    __tablename__ = "specifications"
    __table_args__ = (UniqueConstraint("model_id", "key", name="uq_specifications_model_key"),)
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("product_models.id"), index=True)
    key: Mapped[str] = mapped_column(String(80))
    value: Mapped[str] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class ProductImage(Base):
    __tablename__ = "product_images"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("product_models.id"), index=True)
    url: Mapped[str] = mapped_column(String(500))
    alt: Mapped[str] = mapped_column(String(200), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

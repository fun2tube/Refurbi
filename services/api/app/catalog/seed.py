"""Demo catalogue seed (idempotent). Model names and storage/RAM configurations are public
product facts; no prices, ratings, photos or descriptions are invented. Review before launch."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.catalog.models import Brand, ProductModel, ProductVariant
from app.catalog.schemas import model_slug, slugify

# brand -> [(model name, release year, 5G, [(ram_gb, storage_gb), ...])]
SEED: dict[str, list[tuple[str, int, bool, list[tuple[int, int]]]]] = {
    "Apple": [
        ("iPhone 11", 2019, False, [(4, 64), (4, 128), (4, 256)]),
        ("iPhone 12", 2020, True, [(4, 64), (4, 128), (4, 256)]),
        ("iPhone 13", 2021, True, [(4, 128), (4, 256), (4, 512)]),
        ("iPhone 14", 2022, True, [(6, 128), (6, 256), (6, 512)]),
        ("iPhone 15", 2023, True, [(6, 128), (6, 256), (6, 512)]),
    ],
    "Samsung": [
        ("Galaxy S21", 2021, True, [(8, 128), (8, 256)]),
        ("Galaxy S22", 2022, True, [(8, 128), (8, 256)]),
        ("Galaxy S23", 2023, True, [(8, 128), (8, 256)]),
        ("Galaxy A52s 5G", 2021, True, [(6, 128), (8, 128), (8, 256)]),
        ("Galaxy A34 5G", 2023, True, [(6, 128), (8, 128), (8, 256)]),
        ("Galaxy A53 5G", 2022, True, [(6, 128), (8, 128), (8, 256)]),
        ("Galaxy A54 5G", 2023, True, [(8, 128), (8, 256)]),
    ],
    "OnePlus": [
        ("OnePlus 9", 2021, True, [(8, 128), (12, 256)]),
        ("OnePlus 10 Pro", 2022, True, [(8, 128), (12, 256)]),
        ("OnePlus 11", 2023, True, [(8, 128), (16, 256)]),
    ],
}


def seed_catalog(db: Session) -> None:
    for brand_name, models in SEED.items():
        slug = slugify(brand_name)
        brand = db.scalar(select(Brand).where(Brand.slug == slug))
        if brand is None:
            brand = Brand(slug=slug, name=brand_name)
            db.add(brand)
            db.flush()
        for name, year, is_5g, configs in models:
            mslug = model_slug(brand_name, name)
            model = db.scalar(select(ProductModel).where(ProductModel.slug == mslug))
            if model is None:
                model = ProductModel(
                    brand_id=brand.id, slug=mslug, name=name, release_year=year, is_5g=is_5g
                )
                db.add(model)
                db.flush()
            for ram, storage in configs:
                sku = f"{mslug}-{storage}gb-{ram}gb-ram"
                if not db.scalar(select(ProductVariant.id).where(ProductVariant.sku == sku)):
                    db.add(
                        ProductVariant(model_id=model.id, sku=sku, storage_gb=storage, ram_gb=ram)
                    )
    db.commit()

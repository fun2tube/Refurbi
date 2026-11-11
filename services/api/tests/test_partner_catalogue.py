import json

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.catalog.models import ProductModel
from app.core.db import Base
from app.counters.models import Counter
from app.inventory.models import Device, DevicePhoto
from app.partners.catalogue import PACKAGED, SNAPSHOT, import_snapshot, parse_product
from app.preview_seed import seed_preview
from app.seed import seed_rbac

CDN = "https://cdn.shopify.com/s/files/1/x/files/a.jpg"


def prod(title, ptype="Refurbished Mobiles", price="7499.00", pid=1):
    return {
        "id": pid,
        "title": title,
        "product_type": ptype,
        "variants": [{"price": price}],
        "images": [{"src": CDN}],
    }


def test_parses_refurbished_phone():
    p = parse_product(prod("Realme 8i 64GB 4GB RAM Space Black (Refurbished)"))
    assert (p.brand, p.name, p.storage_gb, p.ram_gb, p.color) == (
        "Realme",
        "8i",
        64,
        4,
        "Space Black",
    )
    assert p.price_paise == 749900 and p.images == [CDN]


def test_5g_after_ram_and_multi_storage():
    p = parse_product(prod("Google Pixel 8A 128GB 8GB RAM 5G Obsidian (Good Condition)"))
    assert p.is_5g and p.name == "Pixel 8A" and p.color == "Obsidian"
    q = parse_product(prod("Apple iPhone 13 128GB/256GB (Refurbished)"))
    assert q.storage_gb == 128 and q.ram_gb is None


def test_pre_owned_phone_ok_but_dead_combo_and_other_types_skipped():
    assert parse_product(prod("Used Samsung Galaxy F62 128GB 6GB RAM Laser Blue", "Pre Owned"))
    assert parse_product(prod("Dead Realme C35 Blue", "Pre Owned")) is None
    assert parse_product(prod("Combo of 2 Dead Samsung Galaxy A7 Mobiles", "Pre Owned")) is None
    assert parse_product(prod("Dell Latitude 8GB 256GB", "Laptop")) is None
    assert parse_product(prod("Apple iPhone 12 128GB", price="0.00")) is None


def test_non_cdn_images_dropped():
    p = prod("Realme 8i 64GB 4GB RAM Black")
    p["images"] = [{"src": "http://evil.example/x.jpg"}]
    assert parse_product(p).images == []


def test_packaged_snapshot_matches_canonical_and_has_no_partner_name():
    assert PACKAGED.read_text() == SNAPSHOT.read_text()
    assert "budli" not in PACKAGED.read_text().lower()
    assert len(json.loads(PACKAGED.read_text())) > 100


@pytest.fixture
def factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_import_is_idempotent_and_demo_only(factory, tmp_path):
    snap = tmp_path / "s.json"
    snap.write_text(
        json.dumps(
            [
                prod("Realme 8i 64GB 4GB RAM Space Black (Refurbished)", pid=11),
                prod("Apple iPhone 12 128GB Blue", pid=12, price="21999.00"),
            ]
        )
    )
    with factory() as db:
        seed_rbac(db)
        seed_preview(db)
        before = db.scalar(select(func.count(Device.id)))
        a = import_snapshot(db, snap)
        b = import_snapshot(db, snap)
        assert a["devices"] == 2 and b["devices"] == 0 and b["models"] == 0
        assert db.scalar(select(func.count(Device.id))) == before + 2
        assert db.scalar(select(ProductModel.id).where(ProductModel.slug == "iphone-12"))
        d = db.scalar(select(Device).where(Device.price_paise == 2199900))
        assert d.counter_id in set(db.scalars(select(Counter.id).where(Counter.is_demo.is_(True))))
        assert db.scalar(select(func.count(DevicePhoto.id))) >= 2
        # price change re-import updates in place
        snap.write_text(snap.read_text().replace("21999.00", "20999.00"))
        assert import_snapshot(db, snap)["updated"] == 1


def test_full_snapshot_imports_and_listing_never_names_partner(factory):
    with factory() as db:
        seed_rbac(db)
        seed_preview(db)
        stats = import_snapshot(db)
        assert stats["devices"] > 400
        from app.catalog.models import Brand, ProductModel, ProductVariant
        from app.storefront.router import _unit  # public serialiser

        rows = db.execute(
            select(Device, ProductVariant, ProductModel, Brand, Counter)
            .join(ProductVariant, Device.variant_id == ProductVariant.id)
            .join(ProductModel, ProductVariant.model_id == ProductModel.id)
            .join(Brand, ProductModel.brand_id == Brand.id)
            .join(Counter, Device.counter_id == Counter.id)
            .limit(200)
        ).all()
        out = " ".join(_unit(*r).model_dump_json() for r in rows).lower()
        assert "budli" not in out and "imei" not in out and "cost" not in out

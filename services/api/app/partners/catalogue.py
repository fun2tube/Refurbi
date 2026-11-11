"""Partner catalogue import (phones only). Parses a Shopify-style products.json snapshot into
the catalogue as DEMO data: models, variants, images (partner CDN URLs) and one demo device per
listing whose demo price is the partner price. The partner's name and links are never stored in
the DB or shown publicly. See docs/PARTNER_CONTENT.md. Idempotent: re-running updates in place."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.catalog.models import Brand, ProductImage, ProductModel, ProductVariant
from app.catalog.schemas import model_slug, slugify
from app.counters.models import Counter
from app.inventory import imei as imei_mod
from app.inventory.models import Device, DevicePhoto, DeviceStatus, LocationKind

# Canonical snapshot lives at <repo>/data/partners/budli/phones.json; a packaged copy sits next to
# this module because the API Docker context is services/api only (kept identical by the fetch
# script and a test).
PACKAGED = Path(__file__).with_name("phones_snapshot.json")
SNAPSHOT = Path(__file__).resolve().parents[4] / "data" / "partners" / "budli" / "phones.json"
PHONE_TYPES = {"refurbished mobiles", "pre owned"}
BRANDS = {
    "apple": "Apple",
    "samsung": "Samsung",
    "xiaomi": "Xiaomi",
    "redmi": "Xiaomi",
    "mi": "Xiaomi",
    "poco": "Xiaomi",
    "realme": "Realme",
    "oneplus": "OnePlus",
    "oppo": "Oppo",
    "vivo": "Vivo",
    "motorola": "Motorola",
    "google": "Google",
    "nokia": "Nokia",
    "asus": "Asus",
    "lenovo": "Lenovo",
    "infinix": "Infinix",
    "tecno": "Tecno",
    "iqoo": "iQOO",
    "nothing": "Nothing",
    "honor": "Honor",
    "huawei": "Huawei",
    "lava": "Lava",
    "itel": "Itel",
    "micromax": "Micromax",
    "lg": "LG",
    "sony": "Sony",
    "htc": "HTC",
    "gionee": "Gionee",
    "coolpad": "Coolpad",
    "lyf": "LYF",
}
_STORAGE = re.compile(r"(\d+)\s?(GB|TB)\b", re.I)
_RAM = re.compile(r"(\d+)\s?GB\s?RAM", re.I)
_PAREN = re.compile(r"\([^)]*\)")
_NOISE = re.compile(r"\b(refurbished|used|good condition|global variant device)\b", re.I)
DEMO_IMEI_PREFIX = "98"


@dataclass
class Parsed:
    pid: int
    brand: str
    name: str
    storage_gb: int
    ram_gb: int | None
    color: str | None
    is_5g: bool
    price_paise: int
    images: list[str] = field(default_factory=list)


def _first_int_gb(text: str) -> int | None:
    m = _STORAGE.search(text)
    if not m:
        return None
    return int(m.group(1)) * (1024 if m.group(2).upper() == "TB" else 1)


def parse_product(p: dict) -> Parsed | None:
    """Return a Parsed phone, or None if the listing is not a usable phone."""
    if str(p.get("product_type", "")).strip().lower() not in PHONE_TYPES:
        return None
    raw = p.get("title", "")
    low = raw.lower()
    if low.startswith("dead ") or "combo" in low or " dead " in low:
        return None
    title = _PAREN.sub(" ", raw)  # drops (Refurbished), (Good Condition), (A1688) model codes
    title = re.sub(r"\s+", " ", _NOISE.sub(" ", title)).strip()
    words = title.split()
    brand = BRANDS.get(words[0].lower()) if words else None
    if brand is None:
        return None
    sm = _STORAGE.search(title)
    if sm is None:
        return None
    storage = _first_int_gb(title)
    rm = _RAM.search(title)
    ram = int(rm.group(1)) if rm else None
    head = title[: sm.start()].strip()
    is_5g = bool(re.search(r"\b5G\b", title))
    head = re.sub(r"\b[45]G\b", "", head).strip()
    name = re.sub(r"\s+", " ", head)
    if words[0].lower() in {"redmi", "poco", "mi"} and brand == "Xiaomi":
        name = (
            name if name.lower().startswith(("xiaomi", words[0].lower())) else f"{words[0]} {name}"
        )
    if name.lower().startswith(brand.lower() + " "):
        name = name[len(brand) + 1 :]
    if not name:
        return None
    tail = title[sm.end() :]
    tail = re.sub(r"(\d+\s?(GB|TB)\s?RAM|/\s?\d+\s?GB( RAM)?|\b[45]G\b)", "", tail, flags=re.I)
    tail = re.sub(r"^[\s/]+(\d+GB)?", "", tail).strip(" /-")
    color = tail or None
    v = (p.get("variants") or [{}])[0]
    try:
        price = round(float(v.get("price")) * 100)
    except (TypeError, ValueError):
        return None
    if price <= 0:
        return None
    imgs = [i["src"] if isinstance(i, dict) else i for i in p.get("images", [])]
    imgs = [u for u in imgs if u.startswith("https://cdn.shopify.com/")]
    return Parsed(int(p["id"]), brand, name, storage or 0, ram, color, is_5g, price, imgs[:3])


def slim(p: dict) -> dict:
    """Keep only what the importer needs (no descriptions/links) for the committed snapshot."""
    v = (p.get("variants") or [{}])[0]
    return {
        "id": p["id"],
        "title": p["title"],
        "product_type": p["product_type"],
        "variants": [{"price": v.get("price")}],
        "images": [{"src": i["src"]} for i in p.get("images", [])][:3],
    }


def demo_imei(pid: int) -> str:
    body = f"{DEMO_IMEI_PREFIX}{pid % 10**12:012d}"
    for check in range(10):
        if imei_mod.luhn_ok(body + str(check)):
            return body + str(check)
    raise AssertionError("unreachable")


def import_parsed(db: Session, items: list[Parsed]) -> dict[str, int]:
    counters = list(
        db.scalars(select(Counter).where(Counter.is_demo.is_(True)).order_by(Counter.id))
    )
    stats = {"models": 0, "variants": 0, "devices": 0, "updated": 0}
    for n, it in enumerate(items):
        brand = db.scalar(select(Brand).where(Brand.slug == slugify(it.brand)))
        if brand is None:
            brand = Brand(slug=slugify(it.brand), name=it.brand)
            db.add(brand)
            db.flush()
        slug = model_slug(it.brand, it.name)
        model = db.scalar(select(ProductModel).where(ProductModel.slug == slug))
        if model is None:
            model = ProductModel(brand_id=brand.id, slug=slug, name=it.name, is_5g=it.is_5g)
            db.add(model)
            db.flush()
            stats["models"] += 1
        if (
            it.images
            and db.scalar(select(ProductImage.id).where(ProductImage.model_id == model.id)) is None
        ):
            db.add(ProductImage(model_id=model.id, url=it.images[0], alt=f"{it.brand} {it.name}"))
        sku = slugify(f"{slug}-{it.storage_gb}gb-{it.ram_gb or 0}gb-{it.color or 'na'}")[:160]
        variant = db.scalar(select(ProductVariant).where(ProductVariant.sku == sku))
        if variant is None:
            variant = ProductVariant(
                model_id=model.id,
                sku=sku,
                storage_gb=it.storage_gb,
                ram_gb=it.ram_gb,
                color=it.color,
            )
            db.add(variant)
            db.flush()
            stats["variants"] += 1
        imei = demo_imei(it.pid)
        h = imei_mod.hash_imei(imei)
        dev = db.scalar(select(Device).where(Device.imei_hash == h))
        price = it.price_paise  # demo price = partner price
        if dev is not None:
            if dev.price_paise != price:
                dev.price_paise = price
                dev.cost_paise = price * 80 // 100
                stats["updated"] += 1
            continue
        c = counters[n % len(counters)] if counters else None
        dev = Device(
            variant_id=variant.id,
            imei_encrypted=imei_mod.encrypt_imei(imei),
            imei_hash=h,
            imei_last4=imei[-4:],
            grade="ABC"[n % 3],
            battery_health=80 + (n * 7) % 19,
            cost_paise=price * 80 // 100,
            price_paise=price,
            status=DeviceStatus.AVAILABLE.value,
            location_kind=LocationKind.COUNTER.value if c else LocationKind.WAREHOUSE.value,
            counter_id=c.id if c else None,
        )
        db.add(dev)
        db.flush()
        for i, u in enumerate(it.images):
            db.add(DevicePhoto(device_id=dev.id, url=u, kind="cosmetic", sort_order=i))
        stats["devices"] += 1
    db.commit()
    return stats


def import_snapshot(db: Session, path: Path = PACKAGED) -> dict[str, int]:
    if not path.exists():
        return {"models": 0, "variants": 0, "devices": 0, "updated": 0}
    products = json.loads(path.read_text())
    parsed = [x for x in (parse_product(p) for p in products) if x]
    return import_parsed(db, parsed)

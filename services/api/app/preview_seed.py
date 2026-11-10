"""Demo data for one-click preview deployments (APP_ENV=preview). Idempotent.

Everything here is clearly fake: demo counters, demo devices with synthetic Luhn-valid IMEIs,
and dummy prices. Devices are inserted directly (initial state only) because the lifecycle
service (T08) does not exist yet; later changes must go through it.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.catalog.models import ProductVariant
from app.counters.models import Counter
from app.inventory import imei as imei_mod
from app.inventory.models import Device, DeviceStatus, LocationKind
from app.procurement.models import PurchaseOrder, PurchaseOrderLine, Supplier

DEMO_COUNTERS = [
    ("demo-counter-a", "Demo Counter A", "Demo City"),
    ("demo-counter-b", "Demo Counter B", "Demo City"),
    ("demo-counter-c", "Demo Counter C", "Demo Town"),
]
DEVICE_COUNT = 30
GRADES = ["A", "B", "C"]
# status, weight pattern per device index (mostly AVAILABLE, a few other states)
_STATUS_CYCLE = ["AVAILABLE"] * 7 + ["QC_PENDING", "RESERVED", "AVAILABLE"]


def demo_imei(n: int) -> str:
    """Synthetic IMEI for demo device n: 14 digits + Luhn check digit."""
    body = f"99000000{n:06d}"
    for check in range(10):
        if imei_mod.luhn_ok(body + str(check)):
            return body + str(check)
    raise AssertionError("unreachable")


def seed_preview(db: Session) -> dict[str, int]:
    counters = []
    for slug, name, city in DEMO_COUNTERS:
        c = db.scalar(select(Counter).where(Counter.slug == slug))
        if c is None:
            c = Counter(slug=slug, name=name, city=city, is_demo=True, is_verified=True)
            db.add(c)
            db.flush()
        c.is_verified = True  # demo counters are public in preview
        counters.append(c)

    variants = list(db.scalars(select(ProductVariant).order_by(ProductVariant.id)))
    created = 0
    if variants:
        for i in range(DEVICE_COUNT):
            imei = demo_imei(i + 1)
            h = imei_mod.hash_imei(imei)
            if db.scalar(select(Device.id).where(Device.imei_hash == h)):
                continue
            variant = variants[(i * 7) % len(variants)]
            grade = GRADES[i % 3]
            status = _STATUS_CYCLE[i % len(_STATUS_CYCLE)]
            # location: every 4th device in the warehouse, others spread over demo counters
            if i % 4 == 0:
                kind, counter_id = LocationKind.WAREHOUSE.value, None
            else:
                kind, counter_id = LocationKind.COUNTER.value, counters[i % len(counters)].id
            cost = (8_000 + 900 * (i % 20)) * 100  # dummy demo money, integer paise
            price = int(cost * {"A": 1.28, "B": 1.2, "C": 1.12}[grade])
            db.add(
                Device(
                    variant_id=variant.id,
                    imei_encrypted=imei_mod.encrypt_imei(imei),
                    imei_hash=h,
                    imei_last4=imei[-4:],
                    grade=grade,
                    battery_health=96 - (i * 3) % 22 if grade != "C" else 80 - i % 8,
                    cost_paise=cost,
                    price_paise=price if status != "QC_PENDING" else None,
                    status=DeviceStatus(status).value,
                    location_kind=kind,
                    counter_id=counter_id,
                )
            )
            created += 1
    suppliers = 0
    for name, city in [("Demo Supplier One", "Demo City"), ("Demo Supplier Two", "Demo Town")]:
        if db.scalar(select(Supplier.id).where(Supplier.name == name)) is None:
            db.add(
                Supplier(name=name, city=city, notes="Demo data, not a real supplier", is_demo=True)
            )
            suppliers += 1
    db.flush()
    sup = db.scalar(select(Supplier).where(Supplier.name == "Demo Supplier One"))
    if variants and sup and db.scalar(select(PurchaseOrder.id)) is None:
        po = PurchaseOrder(supplier_id=sup.id, status="ORDERED", notes="Demo purchase order")
        po.lines = [
            PurchaseOrderLine(variant_id=variants[0].id, quantity=5, unit_cost_paise=1_200_000),
            PurchaseOrderLine(variant_id=variants[-1].id, quantity=3, unit_cost_paise=2_400_000),
        ]
        db.add(po)
    db.commit()
    return {"counters": len(counters), "devices_created": created, "suppliers": suppliers}

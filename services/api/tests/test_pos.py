# ruff: noqa: F811
from sqlalchemy import select

from app.auth.models import Role, User, UserRole
from app.auth.security import hash_password
from app.counters.models import Counter
from app.inventory.models import Device, DeviceStatus, StockMovement
from tests.test_catalog import PW, client, factory, token  # noqa: F401
from tests.test_qc import mk

PHONE = "9876543210"


def world(factory):
    with factory() as db:
        c1, c2 = Counter(slug="p1", name="P1", is_verified=True), Counter(slug="p2", name="P2")
        db.add_all([c1, c2])
        db.commit()
        ids = (c1.id, c2.id)
    mine = mk(factory, DeviceStatus.AVAILABLE, 900)
    theirs = mk(factory, DeviceStatus.AVAILABLE, 901)
    with factory() as db:
        a, b = db.get(Device, mine), db.get(Device, theirs)
        a.location_kind, a.counter_id, a.price_paise, a.cost_paise = (
            "COUNTER",
            ids[0],
            1_236_000,
            1_000_000,
        )
        b.location_kind, b.counter_id, b.price_paise = "COUNTER", ids[1], 900_000
        db.commit()
    return ids, mine, theirs


def partner(client, factory, email, counter):
    with factory() as db:
        u = User(email=email, password_hash=hash_password(PW))
        db.add(u)
        db.flush()
        rid = db.scalar(select(Role.id).where(Role.code == "counter_partner"))
        db.add(UserRole(user_id=u.id, role_id=rid, counter_id=counter))
        db.commit()
    r = client.post("/auth/login", json={"email": email, "password": PW})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_scoping_and_no_sensitive_fields(client, factory):
    (c1, c2), mine, theirs = world(factory)
    h = partner(client, factory, "pp@x.in", c1)
    r = client.get(f"/pos/counters/{c1}/stock", headers=h)
    assert r.status_code == 200 and [x["device_id"] for x in r.json()] == [mine]
    for bad in ("cost", "imei_encrypted", "supplier", "commission"):
        assert bad not in r.text
    assert client.get(f"/pos/counters/{c2}/stock", headers=h).status_code == 403
    assert client.get(f"/pos/counters/{c1}/stock").status_code == 401
    assert client.get(f"/pos/counters/{c1}/stock?q=zzz", headers=h).json() == []
    body = {
        "device_id": theirs,
        "customer_name": "A",
        "customer_phone": PHONE,
        "payment_mode": "CASH",
    }
    assert client.post(f"/pos/counters/{c2}/sales", headers=h, json=body).status_code == 403
    assert client.post(f"/pos/counters/{c1}/sales", headers=h, json=body).status_code == 404


def test_sale_flow_upi_invoice_whatsapp(client, factory):
    (c1, _), mine, _ = world(factory)
    h = partner(client, factory, "pq@x.in", c1)
    body = {"device_id": mine, "customer_name": "Asha", "customer_phone": PHONE,
            "payment_mode": "UPI", "payment_ref": "T123"}  # fmt: skip
    r = client.post(f"/pos/counters/{c1}/sales", headers=h, json=body)
    assert r.status_code == 201, r.text
    j = r.json()
    assert j["total_paise"] == 1_236_000 and j["invoice_number"].startswith("DEMO/")
    assert j["upi_uri"].startswith("upi://pay?pa=") and "am=12360.00" in j["upi_uri"]
    assert j["whatsapp_url"].startswith("https://wa.me/919876543210?text=")
    for bad in ("cost", "margin", "imei"):
        assert bad not in r.text
    with factory() as db:
        assert db.get(Device, mine).status == "SOLD"
        assert db.scalars(select(StockMovement).where(StockMovement.to_status == "SOLD")).first()
    pdf = client.get(j["invoice_pdf_url"], headers=h)
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"
    assert len(client.get(f"/pos/counters/{c1}/sales", headers=h).json()) == 1
    # stock no longer lists it; double sale rejected
    assert client.get(f"/pos/counters/{c1}/stock", headers=h).json() == []
    assert client.post(f"/pos/counters/{c1}/sales", headers=h, json=body).status_code == 409


def test_validation(client, factory):
    (c1, _), mine, _ = world(factory)
    h = partner(client, factory, "pr@x.in", c1)
    base = {
        "device_id": mine,
        "customer_name": "A",
        "customer_phone": PHONE,
        "payment_mode": "CASH",
    }
    for bad in ({"customer_phone": "123"}, {"payment_mode": "BITCOIN"}, {"customer_name": ""}):
        r = client.post(f"/pos/counters/{c1}/sales", headers=h, json={**base, **bad})
        assert r.status_code == 422
    adm = token(client, factory, "pa@x.in", "admin")  # global admin may sell too
    r = client.post(f"/pos/counters/{c1}/sales", headers=adm, json={**base, "payment_mode": "CARD"})
    assert r.status_code == 201 and "upi_uri" not in r.json()

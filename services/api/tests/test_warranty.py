# ruff: noqa: F811
from datetime import date

from app.inventory.models import Device
from app.warranty import router as wr
from app.warranty.models import Warranty
from app.warranty.service import add_months
from tests.test_catalog import client, factory, token  # noqa: F401
from tests.test_pos import PHONE, partner, world


def test_add_months_edge_cases():
    assert add_months(date(2026, 8, 31), 6) == date(2027, 2, 28)
    assert add_months(date(2026, 11, 10), 6) == date(2027, 5, 10)
    assert add_months(date(2026, 11, 10), 12) == date(2027, 11, 10)


def sale(client, factory, email="wp@x.in"):
    (c1, _), mine, _ = world(factory)
    h = partner(client, factory, email, c1)
    body = {"device_id": mine, "customer_name": "Asha K", "customer_phone": PHONE,
            "payment_mode": "CASH"}  # fmt: skip
    r = client.post(f"/pos/counters/{c1}/sales", headers=h, json=body)
    assert r.status_code == 201, r.text
    return r.json()["invoice_number"], mine


def test_auto_created_and_public_lookup_has_no_pii(client, factory):
    wr._hits.clear()
    inv, did = sale(client, factory)
    with factory() as db:
        w = db.query(Warranty).one()
        assert w.device_id == did and w.months == 6 and w.ends_on > w.starts_on
    r = client.post("/public/warranty/lookup", json={"phone": PHONE, "invoice_number": inv})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["active"] is True and j["months"] == 6
    assert set(j) == {"invoice_number", "device", "starts_on", "ends_on", "months", "active"}
    for bad in ("Asha", PHONE, "imei", "cost", "IMEI"):
        assert bad not in r.text
    # wrong phone / wrong invoice give the same 404
    for body in ({"phone": "9000000000", "invoice_number": inv},
                 {"phone": PHONE, "invoice_number": "NOPE/1"}):  # fmt: skip
        assert client.post("/public/warranty/lookup", json=body).status_code == 404


def test_lookup_rate_limited(client):
    wr._hits.clear()
    for _ in range(10):
        client.post("/public/warranty/lookup", json={"phone": PHONE, "invoice_number": "X/1/1"})
    r = client.post("/public/warranty/lookup", json={"phone": PHONE, "invoice_number": "X/1/1"})
    assert r.status_code == 429
    wr._hits.clear()


def test_claims_workflow(client, factory):
    inv, did = sale(client, factory, "wq@x.in")
    adm = token(client, factory, "wa@x.in", "admin")
    assert client.get("/admin/warranty").status_code == 401
    assert (
        client.get(
            "/admin/warranty", headers=token(client, factory, "wt@x.in", "qc_technician")
        ).status_code
        == 403
    )
    ws = client.get(f"/admin/warranty?q={PHONE}", headers=adm).json()
    assert len(ws) == 1 and ws[0]["invoice_number"] == inv
    wid = ws[0]["id"]
    c = client.post(f"/admin/warranty/{wid}/claims", headers=adm, json={"issue": "Screen flickers"})
    assert c.status_code == 201
    cid = c.json()["id"]
    patch = lambda s: client.patch(f"/admin/warranty/claims/{cid}", headers=adm, json={"status": s})  # noqa: E731
    assert patch("RESOLVED").status_code == 409  # must be approved first
    assert patch("APPROVED").json()["status"] == "APPROVED"
    with factory() as db:
        assert db.get(Device, did).status == "WARRANTY_HOLD"
    assert patch("REJECTED").status_code == 409
    assert patch("RESOLVED").json()["status"] == "RESOLVED"
    with factory() as db:
        assert db.get(Device, did).status == "SOLD"
    assert len(client.get("/admin/warranty/claims?status=RESOLVED", headers=adm).json()) == 1
    assert client.get("/admin/warranty", headers=adm).json()[0]["claims"][0]["id"] == cid


def test_expired_warranty_cannot_claim(client, factory):
    sale(client, factory, "wx@x.in")
    with factory() as db:
        w = db.query(Warranty).one()
        w.ends_on = date(2020, 1, 1)
        db.commit()
        wid = w.id
    adm = token(client, factory, "wy@x.in", "admin")
    r = client.post(f"/admin/warranty/{wid}/claims", headers=adm, json={"issue": "Broken"})
    assert r.status_code == 409
    num = client.get("/admin/warranty", headers=adm).json()[0]["invoice_number"]
    r = client.post("/public/warranty/lookup", json={"phone": PHONE, "invoice_number": num})
    assert r.json()["active"] is False

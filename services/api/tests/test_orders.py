# ruff: noqa: F811
import pytest
from sqlalchemy import select

from app.inventory.models import Device
from app.orders.models import Order
from app.reservations import router as rr
from tests.test_catalog import token
from tests.test_checkout import _otp
from tests.test_payments import _held
from tests.test_preview import factory  # noqa: F401
from tests.test_storefront import client  # noqa: F401


@pytest.fixture(autouse=True)
def _reset_limits():
    rr._hits.clear()


def _paid(c):
    uid, j = _held(c)
    s = c.post(f"/public/payments/{j['token']}/start").json()
    assert c.post(f"/public/payments/fake/{s['order_id']}/pay").json()["status"] == "PAID"
    return uid, j


def test_payment_creates_order_and_sells_device(client):
    c, f = client
    uid, j = _paid(c)
    with f() as db:
        o = db.scalar(select(Order))
        assert o.status == "PLACED" and o.total_paise == j["total_paise"]
        assert db.get(Device, uid).status == "SOLD"
        tok = o.token
    r = c.get(f"/public/orders/{tok}")
    assert r.status_code == 200
    body = r.json()
    assert body["timeline"][0]["status"] == "PLACED" and body["items"][0]["title"]
    low = r.text.lower()
    for bad in (
        "imei",
        "cost",
        "supplier",
        "commission",
        "b@example.com",
        "demo street",
        "9000000000",
    ):
        assert bad not in low
    assert c.get("/public/orders/nope").status_code == 404


def test_account_orders_need_otp_and_scope_to_email(client):
    c, f = client
    _paid(c)
    assert (
        c.post(
            "/public/account/orders", json={"email": "b@example.com", "otp": "000000"}
        ).status_code
        == 400
    )
    mine = c.post(
        "/public/account/orders", json={"email": "b@example.com", "otp": _otp(c, "b@example.com")}
    )
    assert mine.status_code == 200 and len(mine.json()) == 1
    assert "b@example.com" not in mine.text
    other = c.post(
        "/public/account/orders", json={"email": "z@example.com", "otp": _otp(c, "z@example.com")}
    )
    assert other.json() == []


def test_admin_fulfilment_flow(client):
    c, f = client
    _paid(c)
    assert c.get("/admin/orders").status_code == 401
    h = token(c, f, "adm@example.com", "super_admin")
    oid = c.get("/admin/orders", headers=h).json()[0]["id"]
    states = [c.post(f"/admin/orders/{oid}/advance", headers=h).json()["status"] for _ in range(3)]
    assert states == ["PACKED", "SHIPPED", "DELIVERED"]
    assert c.post(f"/admin/orders/{oid}/advance", headers=h).status_code == 409
    row = c.get("/admin/orders", headers=h).json()[0]
    assert row["tracking_no"].startswith("DEMO")
    with f() as db:
        tok = db.scalar(select(Order)).token
    tl = c.get(f"/public/orders/{tok}").json()
    assert [t["status"] for t in tl["timeline"]] == ["PLACED", "PACKED", "SHIPPED", "DELIVERED"]

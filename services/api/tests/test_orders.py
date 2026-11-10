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


def test_online_order_gets_invoice_and_warranty(client):
    c, f = client
    uid, _ = _paid(c)
    with f() as db:
        tok = db.scalar(select(Order)).token
    b = c.get(f"/public/orders/{tok}").json()
    it = b["items"][0]
    assert it["invoice_number"] and it["warranty_months"] and it["warranty_active"] is True
    low = c.get(f"/public/orders/{tok}").text.lower()
    for bad in ("imei", "cost", "supplier", "commission", "9000000000"):
        assert bad not in low
    r = c.get(f"/public/orders/{tok}/invoice.pdf", params={"number": it["invoice_number"]})
    assert r.status_code == 200 and r.content.startswith(b"%PDF")
    assert (
        c.get("/public/orders/bad/invoice.pdf", params={"number": it["invoice_number"]}).status_code
        == 404
    )
    assert c.get(f"/public/orders/{tok}/invoice.pdf", params={"number": "X/1"}).status_code == 404
    # warranty lookup by phone + invoice works for online orders
    r = c.post(
        "/public/warranty/lookup",
        json={"phone": "9000000000", "invoice_number": it["invoice_number"]},
    )
    assert r.status_code == 200 and r.json()["active"] is True


def test_admin_order_detail(client):
    c, f = client
    _paid(c)
    h = token(c, f, "adm@example.com", "super_admin")
    oid = c.get("/admin/orders", headers=h).json()[0]["id"]
    assert c.get(f"/admin/orders/{oid}").status_code == 401
    d = c.get(f"/admin/orders/{oid}", headers=h).json()
    assert d["items"][0]["invoice_number"] and d["timeline"][0]["status"] == "PLACED"
    assert c.get("/admin/orders/9999", headers=h).status_code == 404


def _delivered(c, f):
    uid, _ = _paid(c)
    h = token(c, f, "adm@example.com", "super_admin")
    oid = c.get("/admin/orders", headers=h).json()[0]["id"]
    for _ in range(3):
        c.post(f"/admin/orders/{oid}/advance", headers=h)
    with f() as db:
        tok = db.scalar(select(Order)).token
    inv = c.get(f"/public/orders/{tok}").json()["items"][0]["invoice_number"]
    return uid, h, tok, inv


def test_return_and_refund_flow(client):
    c, f = client
    uid, h, tok, inv = _delivered(c, f)
    url = f"/public/orders/{tok}/returns"
    assert (
        c.post(
            "/public/orders/bad/returns", json={"invoice_number": inv, "reason": "changed mind"}
        ).status_code
        == 404
    )
    assert c.post(url, json={"invoice_number": "X/9", "reason": "changed mind"}).status_code == 404
    assert c.post(url, json={"invoice_number": inv, "reason": "screen flicker"}).status_code == 201
    assert c.post(url, json={"invoice_number": inv, "reason": "again"}).status_code == 409
    assert c.get(f"/public/orders/{tok}").json()["items"][0]["return_status"] == "REQUESTED"
    assert c.get("/admin/returns").status_code == 401
    rid = c.get("/admin/returns", headers=h).json()[0]["id"]
    # cannot skip steps
    assert c.post(f"/admin/returns/{rid}/refund", json={}, headers=h).status_code == 409
    assert c.post(f"/admin/returns/{rid}/receive", headers=h).status_code == 409
    assert (
        c.post(f"/admin/returns/{rid}/approve", json={}, headers=h).json()["status"] == "APPROVED"
    )
    assert c.post(f"/admin/returns/{rid}/receive", headers=h).json()["status"] == "RECEIVED"
    with f() as db:
        assert db.get(Device, uid).status == "RETURNED"
    price = c.get("/admin/returns", headers=h).json()[0]["price_paise"]
    assert (
        c.post(
            f"/admin/returns/{rid}/refund", json={"amount_paise": price + 1}, headers=h
        ).status_code
        == 400
    )
    r = c.post(f"/admin/returns/{rid}/refund", json={}, headers=h).json()
    assert (
        r["status"] == "REFUNDED"
        and r["refund_paise"] == price
        and r["refund_ref"].startswith("fake_refund")
    )
    assert c.post(f"/admin/returns/{rid}/refund", json={}, headers=h).status_code == 409
    it = c.get(f"/public/orders/{tok}").json()["items"][0]
    assert (
        it["return_status"] == "REFUNDED"
        and it["refund_paise"] == price
        and it["warranty_active"] is False
    )
    low = c.get(f"/public/orders/{tok}").text.lower()
    assert "refund_ref" not in low and "fake_refund" not in low and "imei" not in low


def test_return_rejected_and_rules(client):
    c, f = client
    uid, _ = _paid(c)  # not delivered yet
    with f() as db:
        tok = db.scalar(select(Order)).token
    inv = c.get(f"/public/orders/{tok}").json()["items"][0]["invoice_number"]
    assert (
        c.post(
            f"/public/orders/{tok}/returns", json={"invoice_number": inv, "reason": "too early"}
        ).status_code
        == 409
    )


def test_return_window_closed(client, monkeypatch):
    c, f = client
    uid, h, tok, inv = _delivered(c, f)
    from app.core.settings import get_settings

    monkeypatch.setattr(get_settings(), "return_window_days", -1)
    r = c.post(f"/public/orders/{tok}/returns", json={"invoice_number": inv, "reason": "too late"})
    assert r.status_code == 400 and "window" in r.text

# ruff: noqa: F811
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.checkout.models import Checkout
from app.inventory.models import Device
from app.reservations import router as rr
from app.reservations.email import FakeEmailSender
from tests.test_preview import factory  # noqa: F401
from tests.test_storefront import client  # noqa: F401


@pytest.fixture(autouse=True)
def _reset_limits():
    rr._hits.clear()


def _otp(c, email):
    FakeEmailSender.outbox.clear()
    c.post("/public/reservations/otp", json={"email": email})
    return FakeEmailSender.outbox[-1]["body"].split("code is ")[1][:6]


def _body(ids, code):
    return {"unit_ids": ids, "name": "T Buyer", "email": "b@example.com", "phone": "9000000000",
            "address_line": "12 Demo Street", "city": "Demoville", "pincode": "560001",
            "otp": code}  # fmt: skip


def test_hold_flow_and_public_safety(client):
    c, f = client
    ids = [u["unit_id"] for u in c.get("/public/units").json()["items"][:2]]
    assert c.post("/public/checkout", json=_body(ids, "000000")).status_code == 400
    r = c.post("/public/checkout", json=_body(ids, _otp(c, "b@example.com")))
    assert r.status_code == 201, r.text
    j = r.json()
    assert j["status"] == "HOLD" and len(j["items"]) == 2 and 800 < j["seconds_left"] <= 900
    assert j["delivery"]["estimate_only"] is True
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
    g = c.get(f"/public/checkout/{j['token']}")
    assert g.status_code == 200 and "b@example.com" not in g.text
    # held units vanish from stock and a second buyer cannot take them
    left = {u["unit_id"] for u in c.get("/public/units").json()["items"]}
    assert not left & set(ids)
    assert (
        c.post("/public/checkout", json=_body(ids[:1], _otp(c, "x@example.com"))).status_code == 404
    )
    # cancel releases
    assert c.post(f"/public/checkout/{j['token']}/cancel").json()["status"] == "CANCELLED"
    assert set(ids) <= {u["unit_id"] for u in c.get("/public/units").json()["items"]}


def test_hold_expires_after_15_minutes(client):
    c, f = client
    uid = c.get("/public/units").json()["items"][0]["unit_id"]
    j = c.post("/public/checkout", json=_body([uid], _otp(c, "b@example.com"))).json()
    with f() as db:
        row = db.scalar(select(Checkout))
        row.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        db.commit()
    assert c.get(f"/public/checkout/{j['token']}").json()["status"] == "EXPIRED"
    with f() as db:
        assert db.get(Device, uid).status == "AVAILABLE"


def test_validation_cart_and_delivery(client):
    c, f = client
    assert c.get("/public/delivery-estimate?pincode=560001").json()["min_days"] >= 1
    assert c.get("/public/delivery-estimate?pincode=12").status_code == 422
    uid = c.get("/public/units").json()["items"][0]["unit_id"]
    bad = _body([uid], "123456") | {"pincode": "0123"}
    assert c.post("/public/checkout", json=bad).status_code == 422
    cart = c.get(f"/public/cart?ids={uid},999999").json()
    assert cart[0]["available"] and cart[0]["price_paise"] and not cart[1]["available"]
    assert c.get("/public/checkout/nope").status_code == 404

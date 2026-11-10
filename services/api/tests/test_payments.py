# ruff: noqa: F811
import json
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.checkout.models import Checkout
from app.core.settings import get_settings
from app.inventory.models import Device
from app.payments.gateway import sign
from app.payments.models import Payment, PaymentEvent
from app.reservations import router as rr
from tests.test_checkout import _body, _otp
from tests.test_preview import factory  # noqa: F401
from tests.test_storefront import client  # noqa: F401


@pytest.fixture(autouse=True)
def _reset_limits():
    rr._hits.clear()


def _held(c):
    uid = c.get("/public/units").json()["items"][0]["unit_id"]
    j = c.post("/public/checkout", json=_body([uid], _otp(c, "b@example.com"))).json()
    return uid, j


def _event(order_id, amount, event="payment.captured", pid="pay_1"):
    return json.dumps({"event": event, "payload": {"payment": {"entity": {
        "id": pid, "order_id": order_id, "amount": amount}}}}).encode()  # fmt: skip


def _post(c, body, eid, sig=None):
    sig = sig if sig is not None else sign(body, get_settings().razorpay_webhook_secret)
    return c.post("/public/payments/webhook", content=body,
                  headers={"x-razorpay-signature": sig, "x-razorpay-event-id": eid})  # fmt: skip


def test_signed_webhook_marks_paid_and_is_idempotent(client):
    c, f = client
    uid, j = _held(c)
    s = c.post(f"/public/payments/{j['token']}/start").json()
    assert s["gateway"] == "fake" and s["amount_paise"] == j["total_paise"]
    assert "secret" not in json.dumps(s).lower()
    body = _event(s["order_id"], s["amount_paise"])
    assert _post(c, body, "evt_1", sig="bad").status_code == 400
    assert _post(c, body, "evt_1").json()["result"] == "processed"
    assert _post(c, body, "evt_1").json()["result"] == "duplicate"
    with f() as db:
        assert db.scalar(select(Payment)).status == "PAID"
        assert db.scalar(select(Checkout)).status == "PAID"
        assert db.scalar(select(Device).where(Device.id == uid)).status == "RESERVED"
        assert len(db.scalars(select(PaymentEvent)).all()) == 1
    assert c.get(f"/public/checkout/{j['token']}").json()["status"] == "PAID"
    assert c.post(f"/public/payments/{j['token']}/start").status_code == 409


def test_amount_mismatch_never_fulfils(client):
    c, f = client
    uid, j = _held(c)
    s = c.post(f"/public/payments/{j['token']}/start").json()
    assert _post(c, _event(s["order_id"], 100), "evt_2").status_code == 200
    with f() as db:
        assert db.scalar(select(Payment)).status == "FAILED"
        assert db.scalar(select(Checkout)).status == "HOLD"


def test_late_payment_rehold_or_refund_due(client):
    c, f = client
    uid, j = _held(c)
    s = c.post(f"/public/payments/{j['token']}/start").json()
    with f() as db:
        db.scalar(select(Checkout)).expires_at = datetime.now(UTC) - timedelta(minutes=1)
        db.commit()
    assert c.get(f"/public/checkout/{j['token']}").json()["status"] == "EXPIRED"
    _post(c, _event(s["order_id"], s["amount_paise"]), "evt_3")
    with f() as db:
        assert db.scalar(select(Payment)).status == "PAID"  # phone was still free


def test_fake_pay_demo_and_malformed(client):
    c, f = client
    uid, j = _held(c)
    s = c.post(f"/public/payments/{j['token']}/start").json()
    assert c.post("/public/payments/fake/nope/pay").status_code == 404
    assert c.post(f"/public/payments/fake/{s['order_id']}/pay").json()["status"] == "PAID"
    assert _post(c, b"not json", "evt_9").status_code == 400
    assert c.post("/public/payments/webhook", content=b"{}").status_code == 400

# ruff: noqa: F811
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.inventory.models import Device
from app.reservations import router as rr
from app.reservations.email import FakeEmailSender
from app.reservations.models import Reservation
from app.reservations.service import release_expired
from tests.test_catalog import token
from tests.test_preview import factory  # noqa: F401
from tests.test_storefront import client  # noqa: F401


@pytest.fixture(autouse=True)
def _reset_limits():
    rr._hits.clear()


def _otp(c, email):
    FakeEmailSender.outbox.clear()
    assert c.post("/public/reservations/otp", json={"email": email}).status_code == 202
    return FakeEmailSender.outbox[-1]["body"].split("code is ")[1][:6]


def _unit(c):
    return c.get("/public/units").json()["items"][0]["unit_id"]


def test_reserve_flow_and_no_pii_leak(client):
    c, f = client
    uid = _unit(c)
    body = {"unit_id": uid, "name": "Test Buyer", "email": "buyer@example.com"}
    assert c.post("/public/reservations", json={**body, "otp": "000000"}).status_code == 400
    code = _otp(c, "buyer@example.com")
    r = c.post("/public/reservations", json={**body, "otp": code})
    assert r.status_code == 201, r.text
    text = r.text.lower()
    for w in ("imei", "cost", "email", "buyer", "supplier", "commission"):
        assert w not in text
    assert uid not in [i["unit_id"] for i in c.get("/public/units?page_size=100").json()["items"]]
    with f() as db:
        assert db.get(Device, uid).status == "RESERVED"
    # a second buyer cannot take it; OTP is single use
    code2 = _otp(c, "other@example.com")
    r2 = c.post("/public/reservations", json={**body, "email": "other@example.com", "otp": code2})
    assert r2.status_code == 404
    assert c.post("/public/reservations", json={**body, "otp": code}).status_code in (400, 404)


def test_otp_lockout_and_rate_limit(client):
    c, _ = client
    uid = _unit(c)
    code = _otp(c, "lock@example.com")
    body = {"unit_id": uid, "name": "N", "email": "lock@example.com"}
    for _ in range(5):
        assert c.post("/public/reservations", json={**body, "otp": "111111"}).status_code == 400
    assert c.post("/public/reservations", json={**body, "otp": code}).status_code == 400
    assert c.post("/public/reservations/otp", json={"email": "bad"}).status_code == 422
    codes = [
        c.post("/public/reservations/otp", json={"email": "rl@example.com"}).status_code
        for _ in range(5)
    ]
    assert 429 in codes


def test_expiry_releases_and_admin(client):
    c, f = client
    uid = _unit(c)
    code = _otp(c, "exp@example.com")
    c.post(
        "/public/reservations",
        json={"unit_id": uid, "name": "N", "email": "exp@example.com", "otp": code},
    )
    with f() as db:
        r = db.scalar(select(Reservation))
        r.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        db.commit()
        assert release_expired(db) == 1
        assert db.get(Device, uid).status == "AVAILABLE"
    assert uid in [i["unit_id"] for i in c.get("/public/units?page_size=100").json()["items"]]
    assert c.get("/admin/reservations").status_code == 401
    h = token(c, f, "adm@example.com", "super_admin")
    assert c.get("/admin/reservations", headers=h).status_code == 200
    assert c.post("/admin/reservations/expire", headers=h).json() == {"released": 0}


def test_demo_code_only_with_fake_adapter(client, monkeypatch):
    c, _ = client
    code = c.post("/public/reservations/otp", json={"email": "d@example.com"}).json()["demo_code"]
    assert code and code.isdigit() and len(code) == 6
    monkeypatch.setenv("APP_ENV", "production")
    from app.core.settings import get_settings

    get_settings.cache_clear()
    try:
        assert (
            "demo_code"
            not in c.post("/public/reservations/otp", json={"email": "e@example.com"}).json()
        )
    finally:
        get_settings.cache_clear()

# ruff: noqa: F811

from app.exchange.models import ExchangeLead
from app.exchange.rules import estimate
from tests.test_catalog import client, factory, token  # noqa: F401

GOOD = dict(
    brand="Acme", model_name="Phone X", storage_gb=128, age_band="1_2", screen="perfect",
    body="perfect", battery="good", has_accessories=True, powers_on=True,
)  # fmt: skip


def test_rules():
    base = estimate(**{k: v for k, v in GOOD.items() if k not in ("brand", "model_name")})
    assert base and 0 < base.low_paise < base.high_paise
    worse = estimate(
        age_band="1_2", storage_gb=128, screen="cracked", body="damaged", battery="poor",
        has_accessories=False, powers_on=True,
    )  # fmt: skip
    assert worse.high_paise < base.low_paise
    assert estimate(age_band="1_2", storage_gb=64, screen="perfect", body="perfect",
                    battery="good", has_accessories=True, powers_on=False) is None  # fmt: skip


def test_quote_and_validation(client):
    r = client.post("/public/exchange/quote", json=GOOD)
    assert r.status_code == 200 and r.json()["low_paise"] > 0 and r.json()["is_demo_estimate"]
    assert client.post("/public/exchange/quote", json={**GOOD, "screen": "bad"}).status_code == 422
    r = client.post("/public/exchange/quote", json={**GOOD, "powers_on": False})
    assert r.json()["needs_inspection"] and r.json()["low_paise"] is None


def test_lead_public_response_has_no_pii_and_admin_inbox(client, factory):
    body = {**GOOD, "customer_name": "Test Person", "contact": "9000000000", "city": "Demo"}
    r = client.post("/public/exchange/leads", json=body)
    assert r.status_code == 201
    text = r.text
    assert "9000000000" not in text and "Test Person" not in text
    assert set(r.json()) == {
        "low_paise",
        "high_paise",
        "needs_inspection",
        "is_demo_estimate",
        "disclaimer",
    }
    with factory() as db:
        assert db.query(ExchangeLead).count() == 1
    assert client.get("/admin/exchange/leads").status_code == 401
    cp = token(client, factory, "ex-cp@x.in", "counter_partner")
    assert client.get("/admin/exchange/leads", headers=cp).status_code == 403
    adm = token(client, factory, "ex-ad@x.in", "admin")
    leads = client.get("/admin/exchange/leads", headers=adm).json()
    assert len(leads) == 1 and leads[0]["status"] == "NEW"
    p = client.patch(
        f"/admin/exchange/leads/{leads[0]['id']}", headers=adm, json={"status": "CONTACTED"}
    )
    assert p.json()["status"] == "CONTACTED"
    assert (
        client.patch("/admin/exchange/leads/999", headers=adm, json={"status": "WON"}).status_code
        == 404
    )
    assert (
        client.patch(
            f"/admin/exchange/leads/{leads[0]['id']}", headers=adm, json={"status": "X"}
        ).status_code
        == 422
    )


def test_public_lead_rate_limited(client):
    from app.exchange import router

    router._hits.clear()
    body = {**GOOD, "customer_name": "T", "contact": "9000000001"}
    codes = [client.post("/public/exchange/leads", json=body).status_code for _ in range(12)]
    router._hits.clear()
    assert codes[:10] == [201] * 10 and codes[10] == 429

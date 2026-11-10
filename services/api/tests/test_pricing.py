# ruff: noqa: F811
import pytest
from sqlalchemy import select

from app.inventory.models import AuditLog
from app.pricing.service import landed_cost, margin_bps_at, suggested_price
from tests.test_catalog import client, factory, token  # noqa: F401
from tests.test_qc import mk


def test_worked_examples():
    # Rs 10,000 purchase + Rs 1,500 repair + Rs 500 logistics = Rs 12,000 landed
    landed = landed_cost(1_000_000, 150_000, 50_000)
    assert landed == 1_200_000
    # grade A 25%: 12,000 * 1.25 = 15,000 (already a multiple of Rs 50)
    assert suggested_price(landed, 2500) == 1_500_000
    # grade C 15%: 13,800 exactly
    assert suggested_price(landed, 1500) == 1_380_000
    # rounding up: 12,345 * 1.20 = 14,814 -> Rs 14,850
    assert suggested_price(1_234_500, 2000) == 1_485_000
    assert margin_bps_at(1_500_000, landed) == 2500
    assert margin_bps_at(1, 0) is None


@pytest.fixture
def adm(client, factory):
    return token(client, factory, "pr@x.in", "admin")


def test_permission(client, factory):
    h = token(client, factory, "qc2@x.in", "qc_technician")
    assert client.get("/admin/pricing/rules", headers=h).status_code == 403
    assert client.get("/admin/pricing/rules").status_code == 401


def test_rules_default_and_update(client, adm):
    r = client.get("/admin/pricing/rules", headers=adm).json()
    assert {x["grade"]: x["target_margin_bps"] for x in r} == {"A": 2500, "B": 2000, "C": 1500}
    assert (
        client.put("/admin/pricing/rules/A", json={"target_margin_bps": 3000}, headers=adm).json()[
            "previous"
        ]
        == 2500
    )
    assert (
        client.put("/admin/pricing/rules/Z", json={"target_margin_bps": 1}, headers=adm).status_code
        == 400
    )
    assert (
        client.put(
            "/admin/pricing/rules/A", json={"target_margin_bps": 99999}, headers=adm
        ).status_code
        == 422
    )


def test_costs_suggest_override_audit(client, factory, adm):
    did = mk(factory, n=950)
    from app.inventory.models import Device

    with factory() as db:
        d = db.get(Device, did)
        d.cost_paise, d.grade = 1_000_000, "B"
        db.commit()
    base = f"/admin/pricing/devices/{did}"
    assert (
        client.post(
            f"{base}/costs", json={"kind": "REPAIR", "amount_paise": 150_000}, headers=adm
        ).status_code
        == 201
    )
    b = client.post(
        f"{base}/costs",
        json={"kind": "LOGISTICS", "amount_paise": 50_000, "note": "courier"},
        headers=adm,
    ).json()
    assert b["landed_cost_paise"] == 1_200_000 and b["suggested_price_paise"] == 1_440_000
    assert (
        client.post(
            f"{base}/costs", json={"kind": "PURCHASE", "amount_paise": 5}, headers=adm
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"{base}/costs", json={"kind": "REPAIR", "amount_paise": 0}, headers=adm
        ).status_code
        == 422
    )
    b = client.post(f"{base}/apply-suggested", headers=adm).json()
    assert b["price_paise"] == 1_440_000 and b["margin_bps"] == 2000
    # override below cost needs confirmation, and a reason
    low = {"price_paise": 1_000_000, "reason": "clearance"}
    r = client.put(f"{base}/price", json=low, headers=adm)
    assert r.status_code == 400 and r.json()["error"]["code"] == "below_cost"
    assert client.put(f"{base}/price", json={**low, "reason": ""}, headers=adm).status_code == 422
    assert (
        client.put(f"{base}/price", json={**low, "allow_below_cost": True}, headers=adm).json()[
            "price_paise"
        ]
        == 1_000_000
    )
    with factory() as db:
        acts = [a.action for a in db.scalars(select(AuditLog).where(AuditLog.entity_id == did))]
        assert "price:suggested" in acts and "price:override" in acts and "cost:REPAIR" in acts
        ov = db.scalar(select(AuditLog).where(AuditLog.action == "price:override"))
        assert ov.before == {"price_paise": 1_440_000} and ov.after["reason"] == "clearance"


def test_ungraded_has_no_suggestion(client, factory, adm):
    did = mk(factory, n=951)
    assert (
        client.get(f"/admin/pricing/devices/{did}", headers=adm).json()["suggested_price_paise"]
        is None
    )
    assert (
        client.post(f"/admin/pricing/devices/{did}/apply-suggested", headers=adm).status_code == 400
    )
    assert client.get("/admin/pricing/devices/99999", headers=adm).status_code == 404

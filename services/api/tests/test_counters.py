# ruff: noqa: F811
from datetime import date, timedelta

import pytest

from app.counters.models import CommissionRule, commission_for
from tests.test_catalog import client, factory, token  # noqa: F401


@pytest.fixture
def adm(client, factory):
    return token(client, factory, "ct@x.in", "admin")


def mkc(client, adm, slug="c-one"):
    r = client.post(
        "/admin/counters", headers=adm, json={"slug": slug, "name": "C One", "city": "X"}
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_permissions(client, factory):
    assert client.get("/admin/counters").status_code == 401
    h = token(client, factory, "cp4@x.in", "counter_partner")
    assert client.get("/admin/counters", headers=h).status_code == 403


def test_create_duplicate_and_unverified_by_default(client, adm):
    c = mkc(client, adm)
    assert c["is_verified"] is False
    assert (
        client.post(
            "/admin/counters", headers=adm, json={"slug": "c-one", "name": "dup"}
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/admin/counters", headers=adm, json={"slug": "Bad Slug", "name": "x"}
        ).status_code
        == 422
    )
    r = client.put(
        f"/admin/counters/{c['id']}",
        headers=adm,
        json={"slug": "c-one", "name": "Renamed", "owner_name": "Demo Owner"},
    )
    assert r.json()["name"] == "Renamed" and r.json()["is_verified"] is False


def test_verify_needs_active_agreement_and_gates_public_page(client, adm):
    c = mkc(client, adm)
    cid = c["id"]
    assert client.get("/public/stores/c-one").status_code == 404  # unverified: hidden
    assert (
        client.post(f"/admin/counters/{cid}/verify", headers=adm).json()["error"]["code"]
        == "no_agreement"
    )
    expired = {
        "start_date": str(date.today() - timedelta(days=90)),
        "end_date": str(date.today() - timedelta(days=1)),
    }
    client.post(f"/admin/counters/{cid}/agreements", headers=adm, json=expired)
    assert client.post(f"/admin/counters/{cid}/verify", headers=adm).status_code == 400
    bad = {"start_date": "2026-05-01", "end_date": "2026-01-01"}
    assert (
        client.post(f"/admin/counters/{cid}/agreements", headers=adm, json=bad).status_code == 422
    )
    client.post(
        f"/admin/counters/{cid}/agreements", headers=adm, json={"start_date": str(date.today())}
    )
    assert client.post(f"/admin/counters/{cid}/verify", headers=adm).json()["is_verified"] is True
    assert client.get("/public/stores/c-one").status_code == 200
    assert "c-one" in [s["slug"] for s in client.get("/public/stores").json()]
    client.post(f"/admin/counters/{cid}/unverify", headers=adm)
    assert client.get("/public/stores/c-one").status_code == 404
    assert len(client.get(f"/admin/counters/{cid}/agreements", headers=adm).json()) == 2


def test_public_store_exposes_no_private_fields(client, adm):
    c = mkc(client, adm)
    client.put(
        f"/admin/counters/{c['id']}",
        headers=adm,
        json={"slug": "c-one", "name": "C", "owner_name": "Secret Owner", "phone": "9999999999"},
    )
    client.post(
        f"/admin/counters/{c['id']}/agreements", headers=adm, json={"start_date": str(date.today())}
    )
    client.post(f"/admin/counters/{c['id']}/verify", headers=adm)
    body = client.get("/public/stores/c-one").text
    for secret in ["Secret Owner", "9999999999", "commission", "agreement", "owner_name"]:
        assert secret not in body


def test_commission_rules_validation_and_calculation(client, adm):
    c = mkc(client, adm)
    url = f"/admin/counters/{c['id']}/commission-rules"
    assert (
        client.post(url, headers=adm, json={"kind": "PERCENT", "value": 20000}).status_code == 422
    )
    assert client.post(url, headers=adm, json={"kind": "WEIRD", "value": 1}).status_code == 422
    r = client.post(url, headers=adm, json={"kind": "PERCENT", "value": 500})
    assert r.status_code == 201
    assert client.post(url, headers=adm, json={"kind": "FLAT", "value": 100}).status_code == 409
    assert (
        client.post(f"{url}/{r.json()['id']}/deactivate", headers=adm).json()["is_active"] is False
    )
    assert client.post(url, headers=adm, json={"kind": "FLAT", "value": 100_000}).status_code == 201
    assert (
        client.post(
            url, headers=adm, json={"model_id": 99999, "kind": "FLAT", "value": 1}
        ).status_code
        == 404
    )


def test_commission_for_worked_examples():
    default = CommissionRule(model_id=None, kind="PERCENT", value=500, is_active=True)
    per_model = CommissionRule(model_id=7, kind="FLAT", value=150_000, is_active=True)
    off = CommissionRule(model_id=8, kind="FLAT", value=999, is_active=False)
    rules = [default, per_model, off]
    assert commission_for(rules, 1, 2_000_000) == 100_000  # 5% of Rs 20,000 = Rs 1,000
    assert commission_for(rules, 7, 2_000_000) == 150_000  # model rule wins: flat Rs 1,500
    assert commission_for(rules, 8, 2_000_000) == 100_000  # inactive rule ignored
    assert commission_for([], 1, 2_000_000) == 0
    assert commission_for([default], 1, 1_999_999) == 99_999  # integer rounding down

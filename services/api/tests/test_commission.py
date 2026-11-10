# ruff: noqa: F811
from app.counters.models import CommissionRule
from tests.test_catalog import client, factory, token  # noqa: F401
from tests.test_pos import PHONE, partner, world


def sell(client, h, cid, did):
    body = {"device_id": did, "customer_name": "A", "customer_phone": PHONE, "payment_mode": "CASH"}
    r = client.post(f"/pos/counters/{cid}/sales", headers=h, json=body)
    assert r.status_code == 201, r.text


def test_commission_frozen_statement_and_settlement(client, factory):
    (c1, c2), mine, _ = world(factory)
    with factory() as db:  # 5% default for counter 1 on a Rs 12,360 sale -> Rs 618
        db.add(CommissionRule(counter_id=c1, kind="PERCENT", value=500))
        db.commit()
    h = partner(client, factory, "cm@x.in", c1)
    sell(client, h, c1, mine)
    with factory() as db:  # changing the rule later must not alter the frozen entry
        db.query(CommissionRule).update({"value": 1000})
        db.commit()
    r = client.get(f"/pos/counters/{c1}/commission", headers=h)
    assert r.status_code == 200
    u = r.json()["unsettled"]
    assert u == {"units": 1, "sales_total_paise": 1_236_000, "commission_paise": 61_800,
                 "net_due_to_refurbi_paise": 1_174_200}  # fmt: skip
    for bad in ("cost", "imei", "supplier"):
        assert bad not in r.text
    assert client.get(f"/pos/counters/{c2}/commission", headers=h).status_code == 403
    adm = token(client, factory, "cma@x.in", "admin")
    assert (
        client.get("/admin/commissions/summary", headers=adm).json()[0][
            "unsettled_commission_paise"
        ]
        == 61_800
    )
    assert client.get("/admin/commissions/summary", headers=h).status_code == 403
    s = client.post(
        "/admin/commissions/settlements",
        headers=adm,
        json={"counter_id": c1, "reference": "NEFT-1"},
    )
    assert (
        s.status_code == 201 and s.json()["commission_paise"] == 61_800 and s.json()["units"] == 1
    )
    assert (
        client.post(
            "/admin/commissions/settlements", headers=adm, json={"counter_id": c1}
        ).status_code
        == 409
    )
    st = client.get(f"/admin/commissions/counters/{c1}/statement", headers=adm).json()
    assert st["unsettled"]["units"] == 0 and st["entries"][0]["status"] == "SETTLED"
    assert client.get("/admin/commissions/counters/999/statement", headers=adm).status_code == 404


def test_no_rule_means_zero_commission(client, factory):
    (c1, _), mine, _ = world(factory)
    h = partner(client, factory, "cn@x.in", c1)
    sell(client, h, c1, mine)
    assert (
        client.get(f"/pos/counters/{c1}/commission", headers=h).json()["unsettled"][
            "commission_paise"
        ]
        == 0
    )

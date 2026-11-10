# ruff: noqa: F811
from datetime import UTC, datetime, timedelta

from app.inventory.alerts import compute_alerts
from app.inventory.models import Device, StockMovement
from tests.test_catalog import client, factory, token  # noqa: F401
from tests.test_qc import mk

NOW = datetime(2026, 11, 10, tzinfo=UTC)


def put(factory, did, status, days, kind=None):
    with factory() as db:
        d = db.get(Device, did)
        d.status = status
        if kind:
            d.location_kind = kind
            if kind == "COUNTER":
                d.counter_id = 1
        db.add(
            StockMovement(device_id=did, to_status=status, created_at=NOW - timedelta(days=days))
        )
        db.commit()


def test_thresholds(factory):
    ids = {
        k: mk(factory, n=970 + i)
        for i, k in enumerate(["fresh", "w20", "w21", "c35", "qf", "tr", "tr2", "mm"])
    }
    put(factory, ids["fresh"], "AVAILABLE", 1)
    put(factory, ids["w20"], "AVAILABLE", 20)
    put(factory, ids["w21"], "AVAILABLE", 21)
    put(factory, ids["c35"], "AVAILABLE", 35)
    put(factory, ids["qf"], "QC_FAILED", 0)
    put(factory, ids["tr"], "IN_TRANSIT", 4, "IN_TRANSIT")
    put(factory, ids["tr2"], "IN_TRANSIT", 1, "IN_TRANSIT")
    put(factory, ids["mm"], "QC_PENDING", 2, "COUNTER")
    with factory() as db:
        got = {(a["device_id"], a["kind"]) for a in compute_alerts(db, NOW)}
    assert got == {
        (ids["w21"], "AGEING_WARN"), (ids["c35"], "AGEING_CRITICAL"), (ids["qf"], "QC_FAILED"),
        (ids["tr"], "TRANSIT_STUCK"), (ids["mm"], "COUNTER_MISMATCH"),
    }  # fmt: skip


def test_sold_ignored_and_endpoint(client, factory):
    a = mk(factory, n=990)
    put(factory, a, "SOLD", 100)
    h = token(client, factory, "al@x.in", "admin")
    r = client.get("/admin/inventory/alerts", headers=h).json()
    assert r["total"] == 0
    assert client.get("/admin/inventory/alerts").status_code == 401
    cp = token(client, factory, "al2@x.in", "counter_partner")
    assert client.get("/admin/inventory/alerts", headers=cp).status_code == 403

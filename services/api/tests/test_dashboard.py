# ruff: noqa: F811
from datetime import UTC, datetime, timedelta

from app.dashboard.router import build_dashboard
from app.inventory.models import Device
from tests.test_catalog import client, factory, token  # noqa: F401
from tests.test_commission import sell
from tests.test_pos import partner, world


def test_dashboard_aggregates_and_permissions(client, factory):
    (c1, _), mine, theirs = world(factory)
    h = partner(client, factory, "dash@x.in", c1)
    sell(client, h, c1, mine)  # price 12,36,000p, cost 10,00,000p
    with factory() as db:
        d = db.get(Device, theirs)
        d.created_at = datetime.now(UTC) - timedelta(days=40)
        db.commit()
    adm = token(client, factory, "dasha@x.in", "admin")
    r = client.get("/admin/dashboard", headers=adm)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["today"] == {"units": 1, "sales_paise": 1_236_000, "gross_margin_paise": 236_000}
    assert j["month"]["units"] == 1
    assert j["counter_leaderboard"][0]["sales_paise"] == 1_236_000
    assert {"bucket": "35+", "units": 1} in j["ageing"]
    assert sum(s["units"] for s in j["stock_by_location"]) == 1  # sold one is no longer stock
    assert "imei" not in r.text.lower()
    assert client.get("/admin/dashboard", headers=h).status_code == 403
    assert client.get("/admin/dashboard").status_code == 401


def test_today_is_indian_day(factory):
    with factory() as db:
        # 19:00 UTC on 9 Nov is already 10 Nov in IST
        j = build_dashboard(db, datetime(2026, 11, 9, 19, 0, tzinfo=UTC))
    assert j["today"]["units"] == 0 and j["stock_by_location"] == []

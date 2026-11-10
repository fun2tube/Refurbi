# ruff: noqa: F811
import pytest

from tests.test_catalog import client, factory, token  # noqa: F401
from tests.test_qc import good, mk


@pytest.fixture
def adm(client, factory):
    return token(client, factory, "inv@x.in", "admin")


def test_requires_auth(client, factory):
    assert client.get("/admin/inventory/devices").status_code == 401
    h = token(client, factory, "cp3@x.in", "counter_partner")
    assert client.get("/admin/inventory/devices", headers=h).status_code == 403


def test_list_filters_and_no_full_imei(client, factory, adm):
    a, b = mk(factory, n=960), mk(factory, n=961)
    client.post(f"/admin/qc/devices/{a}/tests", headers=adm,
                json={"checklist": good(), "battery_health": 92, "grade": "A"})  # fmt: skip
    r = client.get("/admin/inventory/devices", headers=adm).json()
    assert r["total"] == 2 and "imei" not in str(r).replace("imei_last4", "")
    assert [
        x["id"] for x in client.get("/admin/inventory/devices?grade=A", headers=adm).json()["items"]
    ] == [a]
    assert (
        client.get("/admin/inventory/devices?status=IMEI_CHECKED", headers=adm).json()["items"][0][
            "id"
        ]
        == b
    )
    assert client.get("/admin/inventory/devices?min_battery=95", headers=adm).json()["total"] == 0
    assert client.get("/admin/inventory/devices?min_age_days=3", headers=adm).json()["total"] == 0
    last4 = r["items"][0]["imei_last4"]
    assert client.get(f"/admin/inventory/devices?q={last4}", headers=adm).json()["total"] >= 1
    assert client.get("/admin/inventory/devices?brand=nope", headers=adm).json()["total"] == 0


def test_detail_timeline(client, factory, adm):
    a = mk(factory, n=962)
    client.post(f"/admin/qc/devices/{a}/tests", headers=adm,
                json={"checklist": good(), "battery_health": 90, "grade": "B"})  # fmt: skip
    d = client.get(f"/admin/inventory/devices/{a}", headers=adm).json()
    assert [t["to"] for t in d["timeline"]] == ["QC_PENDING", "QC_PASSED"]
    assert d["tests"][0]["passed"] is True and d["tests"][0]["is_current"]
    assert client.get("/admin/inventory/devices/9999", headers=adm).status_code == 404

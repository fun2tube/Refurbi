# ruff: noqa: F811
import pytest
from sqlalchemy import select

from app.catalog.models import ProductVariant
from app.inventory.models import Device, StockMovement
from app.procurement.models import ImeiCheck
from tests.test_catalog import client, factory, token  # noqa: F401
from tests.test_lifecycle import _luhn_imei


def _blocked_imei() -> str:
    base = "13579000000000"
    from app.inventory.imei import luhn_ok

    return next(base + str(c) for c in range(10) if luhn_ok(base + str(c)))


@pytest.fixture
def adm(client, factory):  # noqa: F811
    return token(client, factory, "proc@x.in", "admin")


def _po(client, adm, factory, qty=2):
    with factory() as db:
        vid = db.scalar(select(ProductVariant.id))
    s = client.post(
        "/admin/procurement/suppliers", json={"name": "Demo Supplier", "city": "X"}, headers=adm
    )
    assert s.status_code == 201
    r = client.post(
        "/admin/procurement/purchase-orders",
        json={
            "supplier_id": s.json()["id"],
            "lines": [{"variant_id": vid, "quantity": qty, "unit_cost_paise": 1500000}],
        },
        headers=adm,
    )
    assert r.status_code == 201, r.text
    assert r.json()["total_paise"] == qty * 1500000
    return r.json()


def test_requires_permission(client, factory):  # noqa: F811
    assert client.get("/admin/procurement/suppliers").status_code == 401
    h = token(client, factory, "qc@x.in", "qc_technician")
    assert client.get("/admin/procurement/suppliers", headers=h).status_code == 403


def test_supplier_unique_and_update(client, adm):  # noqa: F811
    a = client.post("/admin/procurement/suppliers", json={"name": "S1"}, headers=adm).json()
    assert (
        client.post("/admin/procurement/suppliers", json={"name": "S1"}, headers=adm).status_code
        == 409
    )
    r = client.put(
        f"/admin/procurement/suppliers/{a['id']}", json={"name": "S1", "city": "Pune"}, headers=adm
    )
    assert r.json()["city"] == "Pune"


def test_receive_flow_with_imei_check(client, factory, adm):  # noqa: F811
    po = _po(client, adm, factory)
    pid, lid = po["id"], po["lines"][0]["id"]
    # cannot receive a DRAFT PO
    imei1, imei2 = _luhn_imei(501), _blocked_imei()
    body = {"items": [{"line_id": lid, "imei": imei1}]}
    assert (
        client.post(
            f"/admin/procurement/purchase-orders/{pid}/receive", json=body, headers=adm
        ).status_code
        == 409
    )
    assert (
        client.post(f"/admin/procurement/purchase-orders/{pid}/order", headers=adm).json()["status"]
        == "ORDERED"
    )
    r = client.post(f"/admin/procurement/purchase-orders/{pid}/receive", json=body, headers=adm)
    assert r.status_code == 201, r.text
    assert r.json()["po_status"] == "PARTIALLY_RECEIVED"
    assert r.json()["devices"][0]["status"] == "IMEI_CHECKED"
    r = client.post(
        f"/admin/procurement/purchase-orders/{pid}/receive",
        json={"items": [{"line_id": lid, "imei": imei2}]},
        headers=adm,
    )
    assert r.json()["po_status"] == "RECEIVED"
    assert r.json()["devices"][0]["status"] == "BLACKLISTED"
    assert "imei" not in r.json()["devices"][0]
    with factory() as db:
        assert db.query(ImeiCheck).count() == 2
        d = db.scalar(select(Device).where(Device.cost_paise == 1500000))
        assert d is not None
        moves = [
            m.to_status
            for m in db.scalars(select(StockMovement).where(StockMovement.device_id == d.id))
        ]
        assert moves[0] == "PURCHASED" and "IMEI_CHECKED" in moves
    assert (
        client.get(f"/admin/procurement/purchase-orders/{pid}", headers=adm).json()["lines"][0][
            "received"
        ]
        == 2
    )


def test_receive_validation(client, factory, adm):  # noqa: F811
    po = _po(client, adm, factory, qty=1)
    pid, lid = po["id"], po["lines"][0]["id"]
    client.post(f"/admin/procurement/purchase-orders/{pid}/order", headers=adm)
    url = f"/admin/procurement/purchase-orders/{pid}/receive"
    assert (
        client.post(url, json={"items": [{"line_id": lid, "imei": "123"}]}, headers=adm).status_code
        == 400
    )
    assert (
        client.post(
            url, json={"items": [{"line_id": 999, "imei": _luhn_imei(1)}]}, headers=adm
        ).status_code
        == 404
    )
    two = {
        "items": [{"line_id": lid, "imei": _luhn_imei(2)}, {"line_id": lid, "imei": _luhn_imei(3)}]
    }
    assert client.post(url, json=two, headers=adm).status_code == 409  # over-receive
    ok = {"items": [{"line_id": lid, "imei": _luhn_imei(2)}]}
    assert client.post(url, json=ok, headers=adm).status_code == 201
    # PO now RECEIVED
    assert client.post(url, json=ok, headers=adm).status_code == 409


def test_duplicate_imei_rejected(client, factory, adm):  # noqa: F811
    po = _po(client, adm, factory, qty=3)
    pid, lid = po["id"], po["lines"][0]["id"]
    client.post(f"/admin/procurement/purchase-orders/{pid}/order", headers=adm)
    url = f"/admin/procurement/purchase-orders/{pid}/receive"
    dup = {
        "items": [{"line_id": lid, "imei": _luhn_imei(7)}, {"line_id": lid, "imei": _luhn_imei(7)}]
    }
    assert client.post(url, json=dup, headers=adm).status_code == 409
    one = {"items": [{"line_id": lid, "imei": _luhn_imei(7)}]}
    assert client.post(url, json=one, headers=adm).status_code == 201
    assert client.post(url, json=one, headers=adm).status_code == 409


def test_cancel(client, factory, adm):  # noqa: F811
    po = _po(client, adm, factory)
    assert (
        client.post(f"/admin/procurement/purchase-orders/{po['id']}/cancel", headers=adm).json()[
            "status"
        ]
        == "CANCELLED"
    )
    assert (
        client.post(f"/admin/procurement/purchase-orders/{po['id']}/order", headers=adm).status_code
        == 409
    )

# ruff: noqa: F811
from sqlalchemy import select

from app.auth.models import Role, User, UserRole
from app.auth.security import hash_password
from app.counters.models import Counter
from app.inventory.models import Device, DeviceStatus, StockMovement
from tests.test_catalog import PW, client, factory, token  # noqa: F401
from tests.test_qc import mk


def setup(factory, n=1, base=900):
    with factory() as db:
        c = Counter(slug="c1", name="C1", is_verified=True)
        db.add(c)
        db.commit()
        cid = c.id
    ids = [mk(factory, DeviceStatus.AVAILABLE, base + i) for i in range(n)]
    return cid, ids


def test_auth(client, factory):
    assert client.get("/admin/transfers").status_code == 401
    h = token(client, factory, "tp@x.in", "qc_technician")
    assert client.post("/admin/transfers", headers=h, json={}).status_code == 403


def test_full_flow_warehouse_to_counter(client, factory):
    cid, ids = setup(factory, 2)
    h = token(client, factory, "ta@x.in", "admin")
    r = client.post("/admin/transfers", headers=h, json={"to_counter_id": cid, "device_ids": ids})
    assert r.status_code == 201, r.text
    t = r.json()
    assert "imei" not in r.text.replace("imei_last4", "")
    # pending transfer blocks a duplicate
    r2 = client.post(
        "/admin/transfers", headers=h, json={"to_counter_id": cid, "device_ids": ids[:1]}
    )
    assert r2.status_code == 409
    assert (
        client.post(f"/admin/transfers/{t['id']}/approve", headers=h).json()["status"]
        == "IN_TRANSIT"
    )
    with factory() as db:
        assert db.get(Device, ids[0]).status == "IN_TRANSIT"
    # partial receive
    r = client.post(f"/admin/transfers/{t['id']}/receive", headers=h, json={"device_ids": [ids[0]]})
    assert r.json()["status"] == "IN_TRANSIT"
    r = client.post(f"/admin/transfers/{t['id']}/receive", headers=h)
    assert r.json()["status"] == "RECEIVED"
    with factory() as db:
        d = db.get(Device, ids[1])
        assert (d.status, d.location_kind, d.counter_id) == ("AVAILABLE", "COUNTER", cid)
        n = len(db.scalars(select(StockMovement).where(StockMovement.device_id == ids[1])).all())
        assert n >= 2
    assert client.post(f"/admin/transfers/{t['id']}/receive", headers=h).status_code == 409


def test_counter_return_and_validation(client, factory):
    cid, ids = setup(factory)
    h = token(client, factory, "tb@x.in", "admin")
    bad = {"from_counter_id": cid, "device_ids": ids}  # device is in warehouse
    assert client.post("/admin/transfers", headers=h, json=bad).status_code in (400, 409, 422)
    assert client.post("/admin/transfers", headers=h,
                       json={"device_ids": ids}).status_code in (400, 422)  # noqa: E501  # fmt: skip
    r = client.post("/admin/transfers", headers=h, json={"to_counter_id": cid, "device_ids": ids})
    tid = r.json()["id"]
    assert client.post(f"/admin/transfers/{tid}/cancel", headers=h).json()["status"] == "CANCELLED"
    assert client.post(f"/admin/transfers/{tid}/approve", headers=h).status_code == 409
    with factory() as db:
        assert db.get(Device, ids[0]).status == "AVAILABLE"


def test_counter_partner_receives_only_own(client, factory):
    cid, ids = setup(factory)
    h = token(client, factory, "tc@x.in", "admin")
    tid = client.post("/admin/transfers", headers=h,
                      json={"to_counter_id": cid, "device_ids": ids}).json()["id"]  # fmt: skip
    client.post(f"/admin/transfers/{tid}/approve", headers=h)

    def scoped(email, counter):
        with factory() as db:
            u = User(email=email, password_hash=hash_password(PW))
            db.add(u)
            db.flush()
            rid = db.scalar(select(Role.id).where(Role.code == "counter_partner"))
            db.add(UserRole(user_id=u.id, role_id=rid, counter_id=counter))
            db.commit()

    with factory() as db:
        c2 = Counter(slug="c2", name="C2", is_verified=True)
        db.add(c2)
        db.commit()
        c2id = c2.id
    scoped("other@x.in", c2id)
    scoped("own@x.in", cid)

    def login(email):
        res = client.post("/auth/login", json={"email": email, "password": PW})
        return {"Authorization": f"Bearer {res.json()['access_token']}"}

    other = login("other@x.in")
    assert client.post(f"/admin/transfers/{tid}/receive", headers=other).status_code == 403
    assert client.get("/admin/transfers", headers=other).json() == []
    mine = login("own@x.in")
    assert len(client.get("/admin/transfers", headers=mine).json()) == 1
    r = client.post(f"/admin/transfers/{tid}/receive", headers=mine)
    assert r.status_code == 200 and r.json()["status"] == "RECEIVED"

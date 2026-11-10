import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import models as m
from app.auth.security import hash_password
from app.catalog.seed import SEED, seed_catalog
from app.core.db import Base, get_session
from app.main import app
from app.seed import seed_rbac

PW = "correct horse battery"
FORBIDDEN = {"imei", "imei_hash", "cost", "cost_paise", "supplier", "commission", "purchase"}


@pytest.fixture
def factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    f = sessionmaker(bind=engine, expire_on_commit=False)
    with f() as db:
        seed_rbac(db)
        seed_catalog(db)
    return f


@pytest.fixture
def client(factory):
    def override():
        with factory() as db:
            yield db

    app.dependency_overrides[get_session] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def token(client, factory, email, role):
    with factory() as db:
        u = m.User(email=email, password_hash=hash_password(PW))
        db.add(u)
        db.flush()
        r = db.query(m.Role).filter_by(code=role).one()
        db.add(m.UserRole(user_id=u.id, role_id=r.id, counter_id=None))
        db.commit()
    res = client.post("/auth/login", json={"email": email, "password": PW})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from keys(v)


def test_seed_has_15_models_and_is_idempotent(client, factory):
    with factory() as db:
        seed_catalog(db)
    res = client.get("/catalog/models?page_size=100")
    assert res.json()["total"] == sum(len(v) for v in SEED.values()) == 15
    assert [b["slug"] for b in client.get("/catalog/brands").json()] == [
        "apple",
        "oneplus",
        "samsung",
    ]


def test_public_list_filter_and_pagination(client):
    res = client.get("/catalog/models?brand=samsung&page_size=2")
    body = res.json()
    assert body["total"] == 7 and len(body["items"]) == 2 and body["total_pages"] == 4
    assert all(i["brand"]["slug"] == "samsung" for i in body["items"])


def test_public_detail_and_whitelist(client):
    res = client.get("/catalog/models/iphone-13")
    assert res.status_code == 200
    body = res.json()
    assert [v["storage_gb"] for v in body["variants"]] == [128, 256, 512]
    assert not (set(keys(body)) & FORBIDDEN)
    assert not any("id" == k for k in keys(body))
    assert client.get("/catalog/models/nope").status_code == 404


def test_public_endpoints_expose_no_sensitive_fields(client):
    for url in ["/catalog/brands", "/catalog/models", "/catalog/models/samsung-galaxy-s22"]:
        res = client.get(url)
        assert res.status_code == 200
        assert not (set(keys(res.json())) & FORBIDDEN), url


def test_admin_requires_auth_and_permission(client, factory):
    assert client.get("/admin/catalog/brands").status_code == 401
    assert client.post("/admin/catalog/brands", json={"name": "X"}).status_code == 401
    h = token(client, factory, "p@x.com", "counter_partner")
    assert client.get("/admin/catalog/brands", headers=h).status_code == 403
    assert client.post("/admin/catalog/brands", json={"name": "X"}, headers=h).status_code == 403
    qc = token(client, factory, "q@x.com", "qc_technician")
    assert client.get("/admin/catalog/brands", headers=qc).status_code == 403


def test_admin_crud_flow(client, factory):
    h = token(client, factory, "a@x.com", "admin")
    b = client.post("/admin/catalog/brands", json={"name": "Google"}, headers=h)
    assert b.status_code == 201 and b.json()["slug"] == "google"
    assert (
        client.post("/admin/catalog/brands", json={"name": "Google"}, headers=h).status_code == 409
    )

    mod = client.post(
        "/admin/catalog/models",
        json={"brand_id": b.json()["id"], "name": "Pixel 7", "release_year": 2022, "is_5g": True},
        headers=h,
    )
    assert mod.status_code == 201 and mod.json()["slug"] == "google-pixel-7"
    slug = "google-pixel-7"

    v = client.post(
        f"/admin/catalog/models/{slug}/variants", json={"storage_gb": 128, "ram_gb": 8}, headers=h
    )
    assert v.status_code == 201 and v.json()["sku"] == "google-pixel-7-128gb-8gb-ram"
    assert (
        client.post(
            f"/admin/catalog/models/{slug}/variants",
            json={"storage_gb": 128, "ram_gb": 8},
            headers=h,
        ).status_code
        == 409
    )
    assert (
        client.post(
            f"/admin/catalog/models/{slug}/variants", json={"storage_gb": 0}, headers=h
        ).status_code
        == 422
    )

    specs = client.put(
        f"/admin/catalog/models/{slug}/specifications",
        json=[{"key": "Display", "value": "demo"}, {"key": "Battery", "value": "demo"}],
        headers=h,
    )
    assert [s["key"] for s in specs.json()] == ["Display", "Battery"]
    dup = client.put(
        f"/admin/catalog/models/{slug}/specifications",
        json=[{"key": "A", "value": "1"}, {"key": "A", "value": "2"}],
        headers=h,
    )
    assert dup.status_code == 409

    img = client.post(
        f"/admin/catalog/models/{slug}/images",
        json={"url": "https://img.example.com/a.jpg", "alt": "front"},
        headers=h,
    )
    assert img.status_code == 201
    bad = client.post(
        f"/admin/catalog/models/{slug}/images", json={"url": "javascript:alert(1)"}, headers=h
    )
    assert bad.status_code == 422

    pub = client.get(f"/catalog/models/{slug}").json()
    assert len(pub["variants"]) == 1 and len(pub["specifications"]) == 2
    assert pub["images"] == [{"url": "https://img.example.com/a.jpg", "alt": "front"}]

    # deactivating a variant hides it publicly; deactivating the model hides the page
    client.patch(f"/admin/catalog/variants/{v.json()['id']}", json={"is_active": False}, headers=h)
    assert client.get(f"/catalog/models/{slug}").json()["variants"] == []
    client.patch(f"/admin/catalog/models/{slug}", json={"is_active": False}, headers=h)
    assert client.get(f"/catalog/models/{slug}").status_code == 404
    assert client.get(f"/admin/catalog/models/{slug}", headers=h).status_code == 200
    assert client.get("/catalog/models?brand=google").json()["total"] == 0


def test_deactivated_brand_hidden(client, factory):
    h = token(client, factory, "a@x.com", "admin")
    bid = next(
        b["id"]
        for b in client.get("/admin/catalog/brands", headers=h).json()
        if b["slug"] == "oneplus"
    )
    client.patch(f"/admin/catalog/brands/{bid}", json={"is_active": False}, headers=h)
    assert "oneplus" not in [b["slug"] for b in client.get("/catalog/brands").json()]
    assert client.get("/catalog/models/oneplus-11").status_code == 404
    assert client.get("/admin/catalog/brands/999", headers=h).status_code in (404, 405)
    assert (
        client.patch("/admin/catalog/brands/999", json={"name": "x"}, headers=h).status_code == 404
    )

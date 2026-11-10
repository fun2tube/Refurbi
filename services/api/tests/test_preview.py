import base64
import hashlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.catalog.seed import seed_catalog
from app.core.db import Base, get_session
from app.core.settings import Settings, get_settings
from app.counters.models import Counter
from app.inventory import imei as imei_mod
from app.inventory.models import Device
from app.preview_seed import DEVICE_COUNT, demo_imei, seed_preview
from app.seed import seed_rbac, seed_super_admin


@pytest.fixture
def factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
def seeded(factory):
    with factory() as db:
        seed_rbac(db)
        seed_catalog(db)
        seed_preview(db)
    return factory


def test_demo_imeis_are_valid_and_unique():
    imeis = {demo_imei(n) for n in range(1, DEVICE_COUNT + 1)}
    assert len(imeis) == DEVICE_COUNT
    assert all(imei_mod.normalise_imei(i) == i for i in imeis)


def test_preview_seed_creates_counters_and_devices_across_grades(seeded):
    with seeded() as db:
        assert db.scalar(select(func.count()).select_from(Counter)) == 3
        assert all(c.is_demo for c in db.scalars(select(Counter)))
        devices = list(db.scalars(select(Device)))
        assert len(devices) == DEVICE_COUNT
        assert {d.grade for d in devices} == {"A", "B", "C"}
        assert {d.location_kind for d in devices} == {"WAREHOUSE", "COUNTER"}
        counter_ids = {c.id for c in db.scalars(select(Counter))}
        assert all(d.counter_id in counter_ids for d in devices if d.counter_id)
        assert all(d.cost_paise > 0 and isinstance(d.cost_paise, int) for d in devices)


def test_preview_seed_is_idempotent(seeded):
    with seeded() as db:
        out = seed_preview(db)
        assert out["devices_created"] == 0
        assert db.scalar(select(func.count()).select_from(Device)) == DEVICE_COUNT
        assert db.scalar(select(func.count()).select_from(Counter)) == 3


def test_demo_admin_can_log_in_with_generated_password(factory):
    pw = "Zm9vYmFyYmF6cXV4Lw+/=generated-by-host"  # host-generated values may contain + / =
    with factory() as db:
        seed_rbac(db)
        seed_super_admin(db, "admin@demo.refurbi", pw)

    def override():
        with factory() as db:
            yield db

    from app.main import app

    app.dependency_overrides[get_session] = override
    try:
        c = TestClient(app)
        r = c.post("/auth/login", json={"email": "admin@demo.refurbi", "password": pw})
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]
        me = c.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "given",
    [
        "postgres://u:p@host:5432/db",
        "postgresql://u:p@host:5432/db",
        "postgresql+psycopg://u:p@host:5432/db",
    ],
)
def test_database_url_normalised_to_psycopg(given):
    s = Settings(database_url=given)
    assert s.database_url == "postgresql+psycopg://u:p@host:5432/db"


def test_cors_origins_accept_bare_hosts_and_urls():
    s = Settings(cors_origins="refurbi-web.onrender.com, https://x.example/ ,http://localhost:3000")
    assert s.cors_origin_list == [
        "https://refurbi-web.onrender.com",
        "https://x.example",
        "http://localhost:3000",
    ]
    assert Settings(cors_origins="").cors_origin_list == ["https://refurbi-web.onrender.com"]


def test_cors_defaults_allow_preview_web_without_env():
    from fastapi.testclient import TestClient

    from app.main import app

    c = TestClient(app)
    hdr = {"Access-Control-Request-Method": "GET"}
    for origin in ("https://refurbi-web.onrender.com", "https://refurbi-web-pr-4.onrender.com"):
        r = c.options("/health", headers={**hdr, "Origin": origin})
        assert r.headers["access-control-allow-origin"] == origin
    for origin in ("https://evil.example", "https://refurbi-web.onrender.com.evil.io"):
        r = c.options("/health", headers={**hdr, "Origin": origin})
        assert "access-control-allow-origin" not in r.headers


def test_preview_flag():
    assert Settings(app_env="preview").is_preview
    assert not Settings(app_env="dev").is_preview


def test_arbitrary_generated_string_works_as_imei_key(monkeypatch):
    raw = "aB3/+random-generated-value-not-a-fernet-key="
    monkeypatch.setattr(get_settings(), "imei_encryption_keys", raw)
    token = imei_mod.encrypt_imei("490154203237518")
    assert imei_mod.decrypt_imei(token) == "490154203237518"
    expected = base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest())
    assert imei_mod._to_fernet_key(raw) == expected


def test_valid_fernet_key_used_as_is():
    key = "ZGV2LW9ubHktaW1laS1rZXktZGV2LW9ubHkta2V5MDA="
    assert imei_mod._to_fernet_key(key) == key.encode()


def test_cors_headers_when_origin_configured(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "web.example.com")
    get_settings.cache_clear()
    import importlib

    import app.main as main

    try:
        main = importlib.reload(main)
        c = TestClient(main.app)
        r = c.options(
            "/health",
            headers={"Origin": "https://web.example.com", "Access-Control-Request-Method": "GET"},
        )
        assert r.headers["access-control-allow-origin"] == "https://web.example.com"
        bad = c.get("/health", headers={"Origin": "https://evil.example"})
        assert "access-control-allow-origin" not in bad.headers
    finally:
        monkeypatch.delenv("CORS_ORIGINS")
        get_settings.cache_clear()
        importlib.reload(main)


def test_public_catalog_does_not_leak_demo_device_data(seeded):
    """Demo devices must stay invisible to public endpoints (no IMEI/cost/supplier)."""
    from app.main import app

    def override():
        with seeded() as db:
            yield db

    app.dependency_overrides[get_session] = override
    try:
        c = TestClient(app)
        body = c.get("/catalog/models").text + c.get("/catalog/brands").text
        for secret in ("imei", "cost_paise", "supplier", "99000000"):
            assert secret not in body.lower()
    finally:
        app.dependency_overrides.clear()

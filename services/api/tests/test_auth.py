from datetime import timedelta

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import models as m
from app.auth.deps import require_permission, user_permissions
from app.auth.router import router
from app.auth.security import (
    create_access_token,
    hash_password,
    utcnow,
    verify_password,
)
from app.core.db import Base, get_session
from app.core.errors import install_error_handlers
from app.core.settings import get_settings
from app.seed import seed_rbac, seed_super_admin

PW = "correct horse battery"


@pytest.fixture
def factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    f = sessionmaker(bind=engine, expire_on_commit=False)
    with f() as db:
        seed_rbac(db)
    return f


@pytest.fixture
def client(factory):
    app = FastAPI()
    install_error_handlers(app)
    app.include_router(router)

    @app.get("/admin/users")
    def users_only(user=Depends(require_permission("users.manage"))):
        return {"ok": True}

    @app.get("/counters/{counter_id}/stock")
    def stock(
        counter_id: int, user=Depends(require_permission("counter.stock.read", "counter_id"))
    ):
        return {"counter": counter_id}

    @app.post("/global-sell")
    def global_sell(user=Depends(require_permission("counter.sell"))):
        return {"ok": True}

    def override():
        with factory() as db:
            yield db

    app.dependency_overrides[get_session] = override
    return TestClient(app)


def make_user(factory, email, role, counter_id=None, active=True):
    with factory() as db:
        u = m.User(email=email, password_hash=hash_password(PW), is_active=active)
        db.add(u)
        db.flush()
        r = db.scalar(select(m.Role).where(m.Role.code == role))
        db.add(m.UserRole(user_id=u.id, role_id=r.id, counter_id=counter_id))
        db.commit()
        return u.id


def login(client, email, password=PW):
    return client.post("/auth/login", json={"email": email, "password": password})


def auth(resp):
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_password_is_argon2id():
    h = hash_password("x")
    assert h.startswith("$argon2id$")
    assert verify_password("x", h) and not verify_password("y", h)
    assert not verify_password("x", "garbage")


def test_login_ok_sets_httponly_cookie(client, factory):
    make_user(factory, "a@example.com", "admin")
    r = login(client, "A@Example.com")
    assert r.status_code == 200
    assert r.json()["user"]["roles"] == [{"code": "admin", "counter_id": None}]
    cookie = r.headers["set-cookie"]
    assert "HttpOnly" in cookie and "refurbi_refresh=" in cookie
    assert "password" not in r.text


def test_login_failures_are_uniform(client, factory):
    make_user(factory, "a@example.com", "admin")
    make_user(factory, "off@example.com", "admin", active=False)
    bad = [
        login(client, "a@example.com", "nope"),
        login(client, "none@example.com"),
        login(client, "off@example.com"),
    ]
    assert all(r.status_code == 401 for r in bad)
    assert len({r.json()["error"]["message"] for r in bad}) == 1


def test_me_requires_valid_token(client, factory):
    make_user(factory, "a@example.com", "admin")
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer junk"}).status_code == 401
    r = login(client, "a@example.com")
    assert client.get("/auth/me", headers=auth(r)).json()["email"] == "a@example.com"


def test_expired_and_forged_tokens_rejected(client, factory):
    uid = make_user(factory, "a@example.com", "admin")
    old = create_access_token(uid, now=utcnow() - timedelta(hours=2))
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {old}"}).status_code == 401
    forged = jwt.encode(
        {"sub": str(uid), "typ": "access", "exp": utcnow() + timedelta(hours=1)},
        "wrong-secret-wrong-secret-wrong-secret",
        algorithm="HS256",
    )
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401
    refresh_typ = jwt.encode(
        {"sub": str(uid), "typ": "refresh", "exp": utcnow() + timedelta(hours=1)},
        get_settings().jwt_secret,
        algorithm="HS256",
    )
    assert (
        client.get("/auth/me", headers={"Authorization": f"Bearer {refresh_typ}"}).status_code
        == 401
    )


def test_refresh_rotates_and_reuse_revokes_family(client, factory):
    make_user(factory, "a@example.com", "admin")
    login(client, "a@example.com")
    first = client.cookies.get("refurbi_refresh")
    r = client.post("/auth/refresh")
    assert r.status_code == 200
    second = client.cookies.get("refurbi_refresh")
    assert second and second != first
    # Replay the old (rotated-out) token: rejected and the whole family is revoked.
    client.cookies.set("refurbi_refresh", first, path="/auth")
    assert client.post("/auth/refresh").status_code == 401
    client.cookies.set("refurbi_refresh", second, path="/auth")
    assert client.post("/auth/refresh").status_code == 401
    with factory() as db:
        assert all(t.revoked_at for t in db.scalars(select(m.RefreshToken)))


def test_refresh_without_cookie_and_expired(client, factory):
    uid = make_user(factory, "a@example.com", "admin")
    assert client.post("/auth/refresh").status_code == 401
    login(client, "a@example.com")
    with factory() as db:
        t = db.scalar(select(m.RefreshToken).where(m.RefreshToken.user_id == uid))
        t.expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
    assert client.post("/auth/refresh").status_code == 401


def test_refresh_tokens_stored_hashed(client, factory):
    make_user(factory, "a@example.com", "admin")
    login(client, "a@example.com")
    raw = client.cookies.get("refurbi_refresh")
    with factory() as db:
        assert all(t.token_hash != raw for t in db.scalars(select(m.RefreshToken)))


def test_logout_revokes(client, factory):
    make_user(factory, "a@example.com", "admin")
    login(client, "a@example.com")
    raw = client.cookies.get("refurbi_refresh")
    assert client.post("/auth/logout").status_code == 204
    client.cookies.set("refurbi_refresh", raw, path="/auth")
    assert client.post("/auth/refresh").status_code == 401


def test_deactivated_user_cannot_refresh_or_use_token(client, factory):
    uid = make_user(factory, "a@example.com", "admin")
    r = login(client, "a@example.com")
    with factory() as db:
        db.get(m.User, uid).is_active = False
        db.commit()
    assert client.post("/auth/refresh").status_code == 401
    assert client.get("/auth/me", headers=auth(r)).status_code == 401


def test_require_permission_global_roles(client, factory):
    make_user(factory, "su@example.com", "super_admin")
    make_user(factory, "ad@example.com", "admin")
    su, ad = login(client, "su@example.com"), login(client, "ad@example.com")
    assert client.get("/admin/users", headers=auth(su)).status_code == 200
    assert client.get("/admin/users", headers=auth(ad)).status_code == 403
    assert client.get("/admin/users").status_code == 401


def test_counter_isolation(client, factory):
    make_user(factory, "p1@example.com", "counter_partner", counter_id=1)
    make_user(factory, "adm@example.com", "admin")
    p1, adm = login(client, "p1@example.com"), login(client, "adm@example.com")
    assert client.get("/counters/1/stock", headers=auth(p1)).status_code == 200
    # Other counter: forbidden.
    assert client.get("/counters/2/stock", headers=auth(p1)).status_code == 403
    # Counter-scoped role never grants a global (counter-less) action.
    assert client.post("/global-sell", headers=auth(p1)).status_code == 403
    # Global role works for every counter.
    assert client.get("/counters/2/stock", headers=auth(adm)).status_code == 200


def test_user_with_roles_at_two_counters(factory):
    make_user(factory, "p@example.com", "counter_partner", counter_id=1)
    with factory() as db:
        u = db.scalar(select(m.User))
        r = db.scalar(select(m.Role).where(m.Role.code == "qc_technician"))
        db.add(m.UserRole(user_id=u.id, role_id=r.id, counter_id=2))
        db.commit()
    with factory() as db:
        u = db.scalar(select(m.User))
        assert "counter.sell" in user_permissions(u, 1)
        assert "counter.sell" not in user_permissions(u, 2)
        assert "inventory.write" in user_permissions(u, 2)
        assert "inventory.write" not in user_permissions(u, 1)
        assert user_permissions(u, None) == set()


def test_seed_is_idempotent_and_super_admin_from_env(factory):
    with factory() as db:
        seed_rbac(db)
        assert seed_super_admin(db, "", "") is None
        u = seed_super_admin(db, "Root@Example.com", PW)
        seed_super_admin(db, "root@example.com", PW)
        assert u.email == "root@example.com"
        assert len(db.scalars(select(m.User)).all()) == 1
        assert len(db.scalars(select(m.UserRole)).all()) == 1
        assert "users.manage" in user_permissions(db.get(m.User, u.id))

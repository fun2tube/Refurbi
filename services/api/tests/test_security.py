import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.router import login_limiter, router
from app.core.db import Base, get_session
from app.core.errors import install_error_handlers
from app.core.security import SecurityHeadersMiddleware


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    app = FastAPI()
    install_error_handlers(app)
    app.add_middleware(SecurityHeadersMiddleware, hsts=True)
    app.include_router(router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    def override():
        with factory() as db:
            yield db

    app.dependency_overrides[get_session] = override
    login_limiter.reset()
    yield TestClient(app)
    login_limiter.reset()


def test_security_headers_on_public_and_private_paths(client):
    r = client.get("/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "referrer-policy" in r.headers and "permissions-policy" in r.headers
    assert r.headers["strict-transport-security"].startswith("max-age=")
    assert "cache-control" not in r.headers
    r = client.post("/auth/login", json={"email": "nobody@example.com", "password": "x"})
    assert r.status_code == 401 and r.headers["cache-control"] == "no-store"


def test_login_throttle_counts_only_failures(client):
    body = {"email": "brute@example.com", "password": "wrong"}
    codes = [client.post("/auth/login", json=body).status_code for _ in range(22)]
    assert codes[:20] == [401] * 20 and codes[20:] == [429, 429]
    # other accounts from the same IP are throttled by the IP key too (20 failures used up)
    r = client.post("/auth/login", json={"email": "other@example.com", "password": "x"})
    assert r.status_code == 429

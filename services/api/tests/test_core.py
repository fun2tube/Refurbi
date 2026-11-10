import json
import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Mapped, Session, mapped_column
from sqlalchemy.pool import StaticPool

from app.core.db import Base
from app.core.errors import ConflictError, NotFoundError, install_error_handlers
from app.core.logging import JsonFormatter, install_request_logging
from app.core.pagination import PageDep, make_page, paginate
from app.core.settings import Settings


class Thing(Base):
    __tablename__ = "things"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


class ThingOut(BaseModel):
    id: int
    name: str


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        s.add_all([Thing(name=f"t{i}") for i in range(45)])
        s.commit()
        yield s


@pytest.fixture
def client(session):
    app = FastAPI()
    install_error_handlers(app)
    install_request_logging(app)

    class Body(BaseModel):
        qty: int

    @app.get("/things")
    def things(params: PageDep):
        rows, total = paginate(session, select(Thing).order_by(Thing.id), params)
        return make_page([ThingOut(id=r.id, name=r.name) for r in rows], total, params)

    @app.get("/nf")
    def nf():
        raise NotFoundError("Device not found")

    @app.get("/conflict")
    def conflict():
        raise ConflictError("IMEI exists", details={"field": "imei"})

    @app.post("/body")
    def body(b: Body):
        return b

    @app.get("/boom")
    def boom():
        raise RuntimeError("secret internals")

    return TestClient(app, raise_server_exceptions=False)


def test_settings_defaults_and_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://x:y@h/db")
    s = Settings(_env_file=None)
    assert s.database_url.endswith("@h/db")
    assert s.default_page_size == 20


def test_pagination_pages(client):
    r = client.get("/things?page=2&page_size=20").json()
    assert r["total"] == 45 and r["total_pages"] == 3
    assert [i["name"] for i in r["items"]][0] == "t20"
    last = client.get("/things?page=3&page_size=20").json()
    assert len(last["items"]) == 5


def test_pagination_caps_and_validation(client):
    assert client.get("/things?page_size=1000").json()["page_size"] == 100
    r = client.get("/things?page=0")
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


def test_error_envelope(client):
    r = client.get("/nf")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"
    assert r.json()["error"]["message"] == "Device not found"
    r = client.get("/conflict")
    assert r.status_code == 409 and r.json()["error"]["details"] == {"field": "imei"}
    assert client.get("/missing").json()["error"]["code"] == "not_found"
    r = client.post("/body", json={"qty": "x"})
    assert r.status_code == 422 and r.json()["error"]["details"][0]["loc"] == ["body", "qty"]


def test_unhandled_error_does_not_leak(client):
    r = client.get("/boom")
    assert r.status_code == 500
    assert r.json()["error"]["code"] == "internal_error"
    assert "secret" not in r.text


def test_request_id_header_and_envelope(client):
    r = client.get("/nf", headers={"x-request-id": "abc123"})
    assert r.headers["x-request-id"] == "abc123"
    assert client.get("/nf").headers["x-request-id"]


def test_json_log_format():
    rec = logging.LogRecord("n", logging.INFO, "f", 1, "hello", None, None)
    rec.status = 200
    out = json.loads(JsonFormatter().format(rec))
    assert out["event"] == "hello" and out["level"] == "INFO" and out["status"] == 200

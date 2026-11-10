import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.db import get_session
from app.inventory.models import Device, DevicePhoto
from app.main import app
from app.preview_seed import seed_preview
from tests.test_preview import factory  # noqa: F401  (reuse in-memory DB fixture)

FORBIDDEN = ("imei", "cost", "supplier", "commission", "purchase", "99000000", "imei_hash")


@pytest.fixture
def client(factory):  # noqa: F811
    from app.catalog.seed import seed_catalog
    from app.seed import seed_rbac

    with factory() as db:
        seed_rbac(db)
        seed_catalog(db)
        seed_preview(db)

    def override():
        with factory() as db:
            yield db

    app.dependency_overrides[get_session] = override
    yield TestClient(app), factory
    app.dependency_overrides.clear()


def _all_text(c: TestClient) -> str:
    urls = [
        "/public/units?page_size=100",
        "/public/models",
        "/public/brands",
        "/public/stores",
    ]
    out = "".join(c.get(u).text for u in urls)
    first = c.get("/public/units").json()["items"][0]["unit_id"]
    out += c.get(f"/public/units/{first}").text
    out += c.get("/public/stores/demo-counter-a").text
    return out.lower()


def test_public_endpoints_never_leak_sensitive_fields(client):
    c, _ = client
    text = _all_text(c)
    for word in FORBIDDEN:
        assert word not in text, word


def test_only_available_priced_devices_listed(client):
    c, f = client
    items = c.get("/public/units?page_size=100").json()["items"]
    assert items
    with f() as db:
        ids = {i["unit_id"] for i in items}
        for d in db.scalars(select(Device)):
            listed = d.id in ids
            assert listed == (d.status == "AVAILABLE" and d.price_paise is not None)


def test_filters_and_sorting(client):
    c, _ = client
    allu = c.get("/public/units?page_size=100").json()
    n = allu["total"]
    a = c.get("/public/units?grade=A&page_size=100").json()["items"]
    assert a and all(u["grade"] == "A" for u in a) and len(a) < n
    asc = [
        u["price_paise"]
        for u in c.get("/public/units?sort=price_asc&page_size=100").json()["items"]
    ]
    assert asc == sorted(asc)
    cap = asc[len(asc) // 2]
    cheap = c.get(f"/public/units?max_price={cap}&page_size=100").json()["items"]
    assert cheap and all(u["price_paise"] <= cap for u in cheap)
    store = c.get("/public/units?store=demo-counter-a&page_size=100").json()["items"]
    assert store and all(u["store"]["slug"] == "demo-counter-a" for u in store)
    assert c.get("/public/units?grade=Z").status_code == 422
    assert c.get("/public/units?page_size=2").json()["total_pages"] >= 2


def test_models_brands_and_stores(client):
    c, _ = client
    models = c.get("/public/models").json()
    assert models and all(m["units_available"] >= 1 and m["from_price_paise"] > 0 for m in models)
    assert {b["slug"] for b in c.get("/public/brands").json()}
    stores = c.get("/public/stores").json()
    assert {s["slug"] for s in stores} == {"demo-counter-a", "demo-counter-b", "demo-counter-c"}
    assert c.get("/public/stores/nope").status_code == 404
    assert c.get("/public/units/999999").status_code == 404


def test_unit_detail_hides_unavailable_and_filters_photo_urls(client):
    c, f = client
    with f() as db:
        unavailable = db.scalar(select(Device).where(Device.status == "QC_PENDING"))
        avail = db.scalar(select(Device).where(Device.status == "AVAILABLE"))
        db.add(DevicePhoto(device_id=avail.id, url="javascript:alert(1)"))
        db.add(DevicePhoto(device_id=avail.id, url="https://cdn.example/x.jpg"))
        db.commit()
        uid, aid = unavailable.id, avail.id
    assert c.get(f"/public/units/{uid}").status_code == 404
    assert c.get(f"/public/units/{aid}").json()["photos"] == ["https://cdn.example/x.jpg"]


def test_text_search(client):
    c, _ = client
    r = c.get("/public/units?q=iphone&page_size=100").json()["items"]
    assert all("iphone" in u["model"]["name"].lower() for u in r)
    assert c.get("/public/units?q=zzzznomatch").json()["total"] == 0
    assert c.get("/public/units?q=%25").status_code == 200

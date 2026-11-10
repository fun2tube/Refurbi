# ruff: noqa: F811
import pytest
from sqlalchemy import select

from app.core.settings import get_settings
from app.inventory.models import Device, DeviceStatus
from app.qc.storage import S3Storage
from app.qc.template import SMARTPHONE_TEMPLATE
from tests.test_catalog import client, factory, token  # noqa: F401
from tests.test_lifecycle import _luhn_imei

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 50


@pytest.fixture
def adm(client, factory):
    return token(client, factory, "qc@x.in", "qc_technician")


@pytest.fixture
def media_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("MEDIA_DIR", str(tmp_path))
    get_settings.cache_clear()
    yield tmp_path
    get_settings.cache_clear()


def mk(factory, status=DeviceStatus.IMEI_CHECKED, n=900):
    from app.catalog.models import ProductVariant
    from app.inventory import imei as im

    with factory() as db:
        i = _luhn_imei(n)
        d = Device(
            variant_id=db.scalar(select(ProductVariant.id)),
            imei_encrypted=im.encrypt_imei(i),
            imei_hash=im.hash_imei(i),
            imei_last4=i[-4:],
            status=status.value,
        )
        db.add(d)
        db.commit()
        return d.id


def good(**over):
    c = {i.key: "pass" for i in SMARTPHONE_TEMPLATE}
    c.update(over)
    return c


def test_auth_required(client, factory):
    assert client.get("/admin/qc/template").status_code == 401
    h = token(client, factory, "cp@x.in", "counter_partner")
    assert client.get("/admin/qc/template", headers=h).status_code == 403


def test_pass_flow_sets_grade_battery_status(client, factory, adm):
    did = mk(factory)
    r = client.post(
        f"/admin/qc/devices/{did}/tests",
        headers=adm,
        json={"checklist": good(biometrics="na"), "battery_health": 91, "grade": "A"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "QC_PASSED" and r.json()["grade"] == "A"
    with factory() as db:
        d = db.get(Device, did)
        assert d.battery_health == 91
    cert = client.get(f"/admin/qc/devices/{did}/certificate", headers=adm).json()
    assert cert["grade"] == "A" and cert["passed"] is True and len(cert["items"]) == 15
    assert "imei" not in cert and len(cert["imei_last4"]) == 4


def test_critical_fail_then_retest(client, factory, adm):
    did = mk(factory)
    r = client.post(
        f"/admin/qc/devices/{did}/tests",
        headers=adm,
        json={"checklist": good(display="fail"), "battery_health": 80},
    )
    assert r.json()["passed"] is False and r.json()["status"] == "QC_FAILED"
    assert r.json()["failed_items"] == ["display"]
    r = client.post(
        f"/admin/qc/devices/{did}/tests",
        headers=adm,
        json={"checklist": good(), "battery_health": 85, "grade": "B"},
    )
    assert r.json()["status"] == "QC_PASSED"


def test_noncritical_fail_still_passes_and_validation(client, factory, adm):
    did = mk(factory)
    url = f"/admin/qc/devices/{did}/tests"
    ok = {"checklist": good(body_condition="fail"), "battery_health": 90, "grade": "C"}
    bad_cases = [
        {**ok, "grade": None},
        {**ok, "grade": "Z"},
        {**ok, "battery_health": 120},
        {**ok, "checklist": {"display": "pass"}},
        {**ok, "checklist": good(display="maybe")},
    ]
    for case in bad_cases:
        assert client.post(url, headers=adm, json=case).status_code in (400, 422)
    assert client.post(url, headers=adm, json=ok).json()["status"] == "QC_PASSED"


def test_wrong_status_rejected(client, factory, adm):
    did = mk(factory, DeviceStatus.PURCHASED)
    r = client.post(
        f"/admin/qc/devices/{did}/tests",
        headers=adm,
        json={"checklist": good(), "battery_health": 90, "grade": "A"},
    )
    assert r.status_code == 409
    r = client.post(
        "/admin/qc/devices/9999/tests",
        headers=adm,
        json={"checklist": good(), "battery_health": 90},
    )
    assert r.status_code == 404


def test_photo_upload_validation_and_serving(client, factory, adm, media_dir):
    did = mk(factory)
    url = f"/admin/qc/devices/{did}/photos"
    r = client.put(url, headers=adm, content=PNG)
    assert r.status_code == 201, r.text
    assert r.json()["url"].startswith("/media/devices/")
    assert client.get(r.json()["url"]).content == PNG
    assert client.put(url, headers=adm, content=b"<html>not an image</html>").status_code == 400
    assert client.put(url, headers=adm, content=b"").status_code == 400
    big = PNG + b"0" * (5 * 1024 * 1024)
    assert client.put(url, headers=adm, content=big).status_code == 400
    assert client.put(url, content=PNG).status_code == 401
    assert client.delete(f"{url}/{r.json()['id']}", headers=adm).status_code == 204


def test_media_path_traversal_blocked(client, media_dir):
    (media_dir.parent / "secret.png").write_bytes(PNG)
    assert client.get("/media/../secret.png").status_code in (404,)
    assert client.get("/media/nothing.png").status_code == 404


def test_s3_request_is_signed():
    from datetime import UTC, datetime

    s = S3Storage("https://acc.r2.cloudflarestorage.com", "b", "AK", "SK", "https://pub.r2.dev")
    req = s.build_request("devices/1/a.png", PNG, "image/png", datetime(2026, 1, 1, tzinfo=UTC))
    assert req.get_method() == "PUT" and req.full_url.endswith("/b/devices/1/a.png")
    auth = req.get_header("Authorization")
    assert auth.startswith("AWS4-HMAC-SHA256 Credential=AK/20260101/auto/s3/aws4_request")
    assert "SK" not in auth

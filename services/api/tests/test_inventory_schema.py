import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.catalog.models import Brand, ProductModel, ProductVariant
from app.core.db import Base
from app.inventory import imei as imei_mod
from app.inventory.models import Device, DeviceStatus, DeviceTest

GOOD = "490154203237518"  # standard Luhn-valid test IMEI


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as s:
        b = Brand(slug="b", name="B")
        s.add(b)
        s.flush()
        m = ProductModel(brand_id=b.id, slug="m", name="M")
        s.add(m)
        s.flush()
        s.add(ProductVariant(model_id=m.id, sku="m-128", storage_gb=128))
        s.commit()
        yield s


def make(db, imei=GOOD, **kw):
    n = imei_mod.normalise_imei(imei)
    d = Device(
        variant_id=1,
        imei_encrypted=imei_mod.encrypt_imei(n),
        imei_hash=imei_mod.hash_imei(n),
        imei_last4=n[-4:],
        **kw,
    )
    db.add(d)
    db.flush()
    return d


def test_status_enum_matches_decision_d7():
    assert {s.value for s in DeviceStatus} == {
        "PURCHASED", "IMEI_CHECKED", "QC_PENDING", "QC_PASSED", "AVAILABLE", "RESERVED",
        "SOLD", "QC_FAILED", "BLACKLISTED", "IN_TRANSIT", "RETURNED", "WARRANTY_HOLD",
        "REPAIR", "WRITTEN_OFF",
    }  # fmt: skip


def test_imei_validation():
    assert imei_mod.normalise_imei("49-0154 2032 37518") == GOOD
    for bad in ["123", "490154203237519", "abcdefghijklmno", ""]:
        with pytest.raises(ValueError):
            imei_mod.normalise_imei(bad)


def test_imei_encrypt_roundtrip_hash_and_rotation(monkeypatch):
    from cryptography.fernet import Fernet

    tok = imei_mod.encrypt_imei(GOOD)
    assert GOOD not in tok and imei_mod.decrypt_imei(tok) == GOOD
    assert imei_mod.hash_imei(GOOD) == imei_mod.hash_imei(GOOD) != GOOD
    new = Fernet.generate_key().decode()
    from app.core.settings import get_settings

    old = get_settings().imei_encryption_keys
    monkeypatch.setattr(get_settings(), "imei_encryption_keys", f"{new},{old}")
    assert imei_mod.decrypt_imei(tok) == GOOD  # old key still decrypts
    rotated = imei_mod.rotate_imei(tok)
    monkeypatch.setattr(get_settings(), "imei_encryption_keys", new)
    assert imei_mod.decrypt_imei(rotated) == GOOD  # works with only the new key
    with pytest.raises(ValueError):
        imei_mod.decrypt_imei(tok)


def test_device_defaults_and_unique_imei(db):
    d = make(db, cost_paise=1500000)
    assert d.status == "PURCHASED" and d.location_kind == "WAREHOUSE" and d.imei_last4 == "7518"
    with pytest.raises(IntegrityError):
        make(db)  # same IMEI hash
    db.rollback()


@pytest.mark.parametrize(
    "kw",
    [
        {"battery_health": 101},
        {"battery_health": -1},
        {"cost_paise": -1},
        {"price_paise": -5},
        {"grade": "Z"},
        {"status": "FLYING"},
        {"location_kind": "COUNTER"},  # counter without counter_id
        {"counter_id": 3},  # counter_id without COUNTER
    ],
)
def test_device_check_constraints(db, kw):
    with pytest.raises(IntegrityError):
        make(db, **kw)
    db.rollback()


def test_counter_location_valid(db):
    d = make(db, location_kind="COUNTER", counter_id=3, grade="A", battery_health=88)
    assert d.counter_id == 3


def test_only_one_current_test_per_device(db):
    d = make(db)
    db.add(DeviceTest(device_id=d.id, checklist={"screen": True}, is_current=True))
    db.flush()
    db.add(DeviceTest(device_id=d.id, checklist={"screen": False}, is_current=True))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_history_tests_allowed(db):
    d = make(db)
    for _ in range(3):
        db.add(DeviceTest(device_id=d.id, checklist={}, is_current=False))
    db.add(DeviceTest(device_id=d.id, checklist={"a": 1}, is_current=True))
    db.flush()
    assert db.execute(text("select count(*) from device_tests")).scalar() == 4

# ruff: noqa: F811  (pytest fixture import)
import itertools
import pathlib
import re

import pytest
from sqlalchemy import func, select

from app.core.errors import NotFoundError
from app.inventory.lifecycle import (
    ALLOWED,
    GuardFailedError,
    InvalidTransitionError,
    Location,
    transition,
)
from app.inventory.models import (
    AuditLog,
    Device,
    DeviceStatus,
    DeviceTest,
    LocationKind,
    StockMovement,
)
from tests.test_inventory_schema import db, make  # noqa: F401  (db fixture)

S = DeviceStatus


def _luhn_imei(n: int) -> str:
    from app.preview_seed import demo_imei

    return demo_imei(n)


_counter = itertools.count(1)


def dev(db, status=S.PURCHASED, **kw):
    d = make(db, imei=_luhn_imei(next(_counter)), **kw)
    d.status = status.value  # test setup only
    db.flush()
    return d


def add_test(db, d, passed):
    db.add(DeviceTest(device_id=d.id, checklist={}, passed=passed, is_current=True))
    db.flush()


def test_every_status_has_a_row_in_the_table():
    assert set(ALLOWED) == set(S)


def test_terminal_states_have_no_exits():
    assert ALLOWED[S.WRITTEN_OFF] == frozenset()


# Exhaustive: every (from, to) pair is either allowed-by-table or rejected as invalid.
@pytest.mark.parametrize("frm", list(S))
@pytest.mark.parametrize("to", list(S))
def test_all_pairs_follow_table(db, frm, to):
    d = dev(db, frm)
    if to in ALLOWED[frm]:
        # Satisfy guards so we test the table, not the guards.
        if to == S.QC_PASSED:
            add_test(db, d, True)
        if to == S.QC_FAILED:
            add_test(db, d, False)
        if frm == S.QC_PASSED and to == S.AVAILABLE:
            db.add(StockMovement(device_id=d.id, to_status="IMEI_CHECKED"))
            d.grade, d.price_paise = "A", 100
        loc = Location(LocationKind.WAREHOUSE) if frm == S.IN_TRANSIT else None
        out = transition(db, d.id, to, reason="because", location=loc)
        assert out.status == to.value
    else:
        with pytest.raises(InvalidTransitionError) as e:
            transition(db, d.id, to, reason="because")
        assert e.value.code == "invalid_transition"
        assert db.get(Device, d.id).status == frm.value


def test_every_transition_writes_movement_and_audit(db):
    d = dev(db, S.PURCHASED)
    transition(db, d.id, S.IMEI_CHECKED, actor_user_id=None)
    mv = db.scalars(select(StockMovement).where(StockMovement.device_id == d.id)).one()
    assert (mv.from_status, mv.to_status) == ("PURCHASED", "IMEI_CHECKED")
    au = db.scalars(select(AuditLog).where(AuditLog.entity_id == d.id)).one()
    assert au.action == "status:PURCHASED->IMEI_CHECKED"
    assert au.before["status"] == "PURCHASED" and au.after["status"] == "IMEI_CHECKED"


def test_rejected_transition_writes_nothing(db):
    d = dev(db, S.PURCHASED)
    with pytest.raises(InvalidTransitionError):
        transition(db, d.id, S.SOLD)
    assert db.scalar(select(func.count()).select_from(StockMovement)) == 0
    assert db.scalar(select(func.count()).select_from(AuditLog)) == 0


def test_unknown_status_and_missing_device(db):
    d = dev(db)
    with pytest.raises(Exception) as e:
        transition(db, d.id, "NOPE")
    assert getattr(e.value, "code", "") == "unknown_status"
    with pytest.raises(NotFoundError):
        transition(db, 99999, S.IMEI_CHECKED)


@pytest.mark.parametrize("to", [S.QC_FAILED, S.BLACKLISTED, S.WRITTEN_OFF])
def test_reason_required(db, to):
    d = dev(db, S.IMEI_CHECKED if to == S.BLACKLISTED else S.QC_PENDING)
    if to == S.QC_FAILED:
        add_test(db, d, False)
    if to == S.WRITTEN_OFF:
        d.status = S.REPAIR.value
    with pytest.raises(GuardFailedError):
        transition(db, d.id, to, reason="  ")
    transition(db, d.id, to, reason="documented")


def test_qc_pass_needs_passing_current_test(db):
    d = dev(db, S.QC_PENDING)
    with pytest.raises(GuardFailedError):
        transition(db, d.id, S.QC_PASSED)
    add_test(db, d, False)
    with pytest.raises(GuardFailedError):
        transition(db, d.id, S.QC_PASSED)


def test_cannot_become_available_without_imei_check_grade_price(db):
    d = dev(db, S.QC_PASSED)
    with pytest.raises(GuardFailedError, match="IMEI check"):
        transition(db, d.id, S.AVAILABLE)
    db.add(StockMovement(device_id=d.id, to_status="IMEI_CHECKED"))
    db.flush()
    with pytest.raises(GuardFailedError, match="grade"):
        transition(db, d.id, S.AVAILABLE)
    d.grade, d.price_paise = "B", 1999900
    assert transition(db, d.id, S.AVAILABLE).status == "AVAILABLE"


def test_full_happy_path_via_service_only(db):
    d = dev(db, S.PURCHASED)
    transition(db, d.id, S.IMEI_CHECKED)
    transition(db, d.id, S.QC_PENDING)
    add_test(db, d, True)
    transition(db, d.id, S.QC_PASSED)
    d.grade, d.price_paise = "A", 2500000
    transition(db, d.id, S.AVAILABLE)
    transition(db, d.id, S.RESERVED)
    transition(db, d.id, S.SOLD)
    assert db.scalar(select(func.count()).select_from(StockMovement)) == 6
    assert db.scalar(select(func.count()).select_from(AuditLog)) == 6


def test_transfer_moves_location_and_requires_destination(db):
    d = dev(db, S.AVAILABLE)
    transition(db, d.id, S.IN_TRANSIT)
    assert (d.location_kind, d.counter_id) == ("IN_TRANSIT", None)
    with pytest.raises(GuardFailedError):
        transition(db, d.id, S.AVAILABLE)
    with pytest.raises(GuardFailedError):
        transition(db, d.id, S.AVAILABLE, location=Location(LocationKind.IN_TRANSIT))
    transition(db, d.id, S.AVAILABLE, location=Location(LocationKind.COUNTER, 7))
    assert (d.location_kind, d.counter_id) == ("COUNTER", 7)
    mv = db.scalars(select(StockMovement).order_by(StockMovement.id.desc())).first()
    assert mv.from_location == "IN_TRANSIT" and mv.to_location == "COUNTER:7"


def test_location_rejected_on_unrelated_transition(db):
    d = dev(db, S.AVAILABLE)
    with pytest.raises(GuardFailedError):
        transition(db, d.id, S.RESERVED, location=Location(LocationKind.WAREHOUSE))


def test_location_value_object_validates():
    with pytest.raises(ValueError):
        Location(LocationKind.COUNTER)
    with pytest.raises(ValueError):
        Location(LocationKind.WAREHOUSE, 3)


def test_only_lifecycle_service_assigns_device_status():
    """Guard rail: no app code outside lifecycle.py may assign `<device>.status = ...`."""
    root = pathlib.Path(__file__).resolve().parents[1] / "app"
    pat = re.compile(r"\b(?:d|device|dev)\.status\s*=[^=]")
    offenders = [
        str(p.relative_to(root))
        for p in root.rglob("*.py")
        if p.name != "lifecycle.py" and pat.search(p.read_text())
    ]
    assert offenders == []

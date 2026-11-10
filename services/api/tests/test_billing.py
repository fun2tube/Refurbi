# ruff: noqa: F811
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import select

from app.billing import gst
from app.billing.models import Invoice
from app.billing.service import issue_invoice
from app.inventory.models import Device, DeviceStatus
from tests.test_catalog import client, factory, token  # noqa: F401
from tests.test_qc import mk


def test_standard_worked_example_intra_and_inter():
    t = gst.compute(gst.STANDARD, selling_paise=1_180_000, rate_bps=1800)
    assert (t.taxable_paise, t.cgst_paise, t.sgst_paise, t.igst_paise) == (
        1_000_000,
        90_000,
        90_000,
        0,
    )
    t = gst.compute(gst.STANDARD, selling_paise=1_180_000, rate_bps=1800, intra_state=False)
    assert (t.taxable_paise, t.cgst_paise, t.sgst_paise, t.igst_paise) == (1_000_000, 0, 0, 180_000)


def test_standard_rounding_sums_exactly():
    t = gst.compute(gst.STANDARD, selling_paise=99_995)
    assert t.taxable_paise == 84_742 and t.tax_paise == 15_253
    assert t.taxable_paise + t.tax_paise == 99_995
    assert t.cgst_paise == 7_626 and t.sgst_paise == 7_627  # odd paisa goes to SGST


def test_margin_worked_example():
    # bought Rs 10,000, sold Rs 12,360 -> margin Rs 2,360 (GST-inclusive) -> GST Rs 360
    t = gst.compute(gst.MARGIN, selling_paise=1_236_000, purchase_paise=1_000_000)
    assert t.margin_paise == 236_000 and t.taxable_paise == 200_000
    assert (t.cgst_paise, t.sgst_paise) == (18_000, 18_000) and t.total_paise == 1_236_000
    t = gst.compute(
        gst.MARGIN, selling_paise=1_236_000, purchase_paise=1_000_000, intra_state=False
    )
    assert t.igst_paise == 36_000


def test_margin_loss_makes_no_tax_and_validation():
    t = gst.compute(gst.MARGIN, selling_paise=500_000, purchase_paise=600_000)
    assert t.tax_paise == 0 and t.margin_paise == 0
    with pytest.raises(ValueError):
        gst.compute("X", selling_paise=1)
    with pytest.raises(ValueError):
        gst.compute(gst.STANDARD, selling_paise=-1)


def test_financial_year():
    assert gst.financial_year(date(2026, 3, 31)) == "2025-26"
    assert gst.financial_year(date(2026, 4, 1)) == "2026-27"
    assert gst.financial_year(date(2099, 11, 1)) == "2099-00"


def test_numbering_gap_free_per_fy_and_rollback(factory):
    ids = [mk(factory, DeviceStatus.SOLD, 900 + i) for i in range(4)]
    kw = dict(selling_paise=1_000_000, customer_name="A", customer_phone="9000000000")
    with factory() as db:
        a = issue_invoice(db, ids[0], when=datetime(2026, 3, 31, 12, tzinfo=UTC), **kw)
        b = issue_invoice(db, ids[1], when=datetime(2026, 4, 1, 12, tzinfo=UTC), **kw)
        c = issue_invoice(db, ids[2], when=datetime(2026, 4, 2, 12, tzinfo=UTC), **kw)
        db.commit()
        assert (a.number, b.number, c.number) == (
            "DEMO/2025-26/000001",
            "DEMO/2026-27/000001",
            "DEMO/2026-27/000002",
        )
    with factory() as db:  # failed issuance rolls back and the number is reused
        issue_invoice(db, ids[3], when=datetime(2026, 4, 3, tzinfo=UTC), **kw)
        db.rollback()
        d = issue_invoice(db, ids[3], when=datetime(2026, 4, 3, tzinfo=UTC), **kw)
        assert d.number == "DEMO/2026-27/000003"
        # one invoice per device
        from app.core.errors import ConflictError

        with pytest.raises(ConflictError):
            issue_invoice(db, ids[0], **kw)


def test_invoice_uses_device_cost_and_api_hides_cost(client, factory):
    did = mk(factory, DeviceStatus.SOLD, 950)
    with factory() as db:
        db.get(Device, did).cost_paise = 1_000_000
        inv = issue_invoice(db, did, selling_paise=1_236_000, customer_name="Asha",
                            customer_phone="9111111111")  # fmt: skip
        db.commit()
        iid = inv.id
        assert inv.margin_paise == 236_000 and inv.cgst_paise == 18_000
    h = token(client, factory, "bill@x.in", "admin")
    r = client.get(f"/admin/invoices/{iid}", headers=h)
    assert r.status_code == 200 and r.json()["total_paise"] == 1_236_000
    assert (
        "cost" not in r.text
        and "margin" not in r.text
        and "imei" not in r.text.replace("imei_last4", "")
    )
    assert len(client.get("/admin/invoices", headers=h).json()) == 1
    p = client.get(f"/admin/invoices/{iid}/pdf", headers=h)
    assert p.status_code == 200 and p.content[:4] == b"%PDF"
    assert client.get("/admin/invoices/999", headers=h).status_code == 404
    assert client.get("/admin/invoices").status_code == 401
    qc = token(client, factory, "qcb@x.in", "qc_technician")
    assert client.get("/admin/invoices", headers=qc).status_code == 403
    with factory() as db:
        assert db.scalar(select(Invoice.id)) == iid

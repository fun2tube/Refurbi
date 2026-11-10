from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app.billing import gst
from app.billing.models import Invoice


def rupees(paise: int) -> str:
    return f"Rs. {paise // 100:,}.{paise % 100:02d}"


def render_pdf(inv: Invoice) -> bytes:
    """Customer-facing invoice. Never prints purchase cost, margin or IMEI beyond last 4."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    y = 285 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(
        20 * mm, y, "TAX INVOICE" if inv.mode == gst.STANDARD else "INVOICE (Margin Scheme)"
    )
    c.setFont("Helvetica", 9)
    s = inv.seller
    for line in (s["name"], s["address"], f"GSTIN: {s['gstin']}"):
        y -= 5 * mm
        c.drawString(20 * mm, y, line)
    y -= 8 * mm
    c.drawString(20 * mm, y, f"Invoice no: {inv.number}")
    c.drawString(120 * mm, y, f"Date: {inv.created_at:%d-%m-%Y}")
    y -= 5 * mm
    c.drawString(20 * mm, y, f"Customer: {inv.customer_name}  ({inv.customer_phone})")
    y -= 10 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(20 * mm, y, "Description")
    c.drawString(120 * mm, y, "HSN")
    c.drawRightString(190 * mm, y, "Amount")
    c.setFont("Helvetica", 9)
    y -= 6 * mm
    c.drawString(20 * mm, y, inv.description[:70])
    c.drawString(120 * mm, y, inv.hsn_code)
    c.drawRightString(190 * mm, y, rupees(inv.total_paise))
    y -= 10 * mm
    if inv.mode == gst.STANDARD:
        rows = [("Taxable value", inv.taxable_paise)]
        if inv.igst_paise:
            rows.append((f"IGST @ {inv.rate_bps / 100:g}%", inv.igst_paise))
        else:
            half = f"{inv.rate_bps / 200:g}%"
            rows += [(f"CGST @ {half}", inv.cgst_paise), (f"SGST @ {half}", inv.sgst_paise)]
        for label, amt in rows:
            c.drawString(120 * mm, y, label)
            c.drawRightString(190 * mm, y, rupees(amt))
            y -= 5 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(120 * mm, y, "Total")
    c.drawRightString(190 * mm, y, rupees(inv.total_paise))
    c.setFont("Helvetica", 8)
    y -= 12 * mm
    if inv.mode == gst.MARGIN:
        c.drawString(20 * mm, y, "Supply of used goods under margin scheme (Rule 32(5)). "
                     "GST is not separately shown; no input tax credit is available.")  # fmt: skip
        y -= 5 * mm
    c.drawString(20 * mm, y, "Warranty terms as printed on the warranty card (to be confirmed).")
    c.showPage()
    c.save()
    return buf.getvalue()

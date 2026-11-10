"""GST calculation for invoices. Pure functions, integer paise only.

Two modes:
- STANDARD: the selling price is GST-inclusive; tax = price - price*100/(100+rate), rounded to
  the nearest paise.
- MARGIN (Rule 32(5), CGST Rules): GST is payable only on the margin (selling price minus
  purchase price, never negative). The margin is treated as GST-inclusive. The tax invoice does
  not show GST separately and the buyer gets no input tax credit.

Intra-state supplies split tax into CGST+SGST (half each, odd paisa to SGST); inter-state use
IGST. All rates/mode choices are CA-confirmation items (see PROGRESS.md founder inputs).
"""

from dataclasses import dataclass

STANDARD = "STANDARD"
MARGIN = "MARGIN"


@dataclass(frozen=True)
class Tax:
    mode: str
    total_paise: int  # amount the customer pays
    taxable_paise: int  # value on which GST is computed (net of tax)
    cgst_paise: int
    sgst_paise: int
    igst_paise: int
    margin_paise: int | None = None  # MARGIN mode only (gross margin, tax inclusive)

    @property
    def tax_paise(self) -> int:
        return self.cgst_paise + self.sgst_paise + self.igst_paise


def _round_div(n: int, d: int) -> int:
    return (n * 2 + d) // (2 * d)  # round half up, non-negative ints


def _split(tax: int, intra_state: bool) -> tuple[int, int, int]:
    if not intra_state:
        return 0, 0, tax
    cgst = tax // 2
    return cgst, tax - cgst, 0


def compute(
    mode: str,
    *,
    selling_paise: int,
    purchase_paise: int = 0,
    rate_bps: int = 1800,
    intra_state: bool = True,
) -> Tax:
    if selling_paise < 0 or purchase_paise < 0 or rate_bps < 0:
        raise ValueError("amounts and rate must be non-negative")
    if mode == STANDARD:
        net = _round_div(selling_paise * 10000, 10000 + rate_bps)
        tax = selling_paise - net
        c, s, i = _split(tax, intra_state)
        return Tax(STANDARD, selling_paise, net, c, s, i)
    if mode == MARGIN:
        margin = max(selling_paise - purchase_paise, 0)
        net_margin = _round_div(margin * 10000, 10000 + rate_bps)
        tax = margin - net_margin
        c, s, i = _split(tax, intra_state)
        return Tax(MARGIN, selling_paise, net_margin, c, s, i, margin_paise=margin)
    raise ValueError(f"unknown GST mode {mode}")


def financial_year(d) -> str:
    """Indian FY (1 Apr - 31 Mar) label, e.g. '2026-27' for 2026-11-10."""
    start = d.year if d.month >= 4 else d.year - 1
    return f"{start}-{(start + 1) % 100:02d}"

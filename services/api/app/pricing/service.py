"""Landed cost and suggested price. All money is integer paise."""

# Placeholder margin targets (bps of landed cost) until the founder sets real ones.
DEFAULT_MARGIN_BPS = {"A": 2500, "B": 2000, "C": 1500}
ROUND_UP_TO_PAISE = 5000  # suggested prices round up to the next Rs 50


def landed_cost(purchase: int, repair: int = 0, logistics: int = 0) -> int:
    return purchase + repair + logistics


def suggested_price(landed: int, margin_bps: int) -> int:
    """landed * (1 + margin), rounded UP to the next Rs 50. Integer arithmetic only."""
    raw = -(-landed * (10_000 + margin_bps) // 10_000)  # ceil division
    return -(-raw // ROUND_UP_TO_PAISE) * ROUND_UP_TO_PAISE


def margin_bps_at(price: int, landed: int) -> int | None:
    """Gross margin on landed cost in bps (rounded down); None if landed is zero."""
    return None if landed <= 0 else (price - landed) * 10_000 // landed

"""Exchange quote rule table (T26).

DEMO PLACEHOLDER VALUES - NOT real buying prices. The founder must replace BASE_BY_AGE_PAISE and the
deductions before launch. Output is an *indicative range*, confirmed after in-store inspection.
Money is integer paise.
"""

from dataclasses import dataclass

DEMO_RULES = True
AGE_BANDS = ("under_1", "1_2", "2_3", "3_4", "over_4")
# Demo base value (paise) for a phone in good condition by age band.
BASE_BY_AGE_PAISE = {
    "under_1": 1_500_000,
    "1_2": 1_000_000,
    "2_3": 600_000,
    "3_4": 350_000,
    "over_4": 150_000,
}
SCREEN_PCT = {"perfect": 0, "scratches": 8, "cracked": 30}
BODY_PCT = {"perfect": 0, "dents": 5, "damaged": 15}
BATTERY_PCT = {"good": 0, "fair": 5, "poor": 12}
NO_ACCESSORIES_PCT = 3
STORAGE_BONUS_PCT = {64: 0, 128: 5, 256: 10, 512: 15}
RANGE_SPREAD_PCT = 10  # +/- around the point estimate


@dataclass(frozen=True)
class Quote:
    low_paise: int
    high_paise: int
    demo: bool = DEMO_RULES


def estimate(
    *,
    age_band: str,
    storage_gb: int,
    screen: str,
    body: str,
    battery: str,
    has_accessories: bool,
    powers_on: bool,
) -> Quote | None:
    """Return an indicative range, or None when the phone does not power on (needs inspection)."""
    if not powers_on:
        return None
    pct = 100 + STORAGE_BONUS_PCT.get(storage_gb, 0)
    pct -= SCREEN_PCT[screen] + BODY_PCT[body] + BATTERY_PCT[battery]
    if not has_accessories:
        pct -= NO_ACCESSORIES_PCT
    pct = max(pct, 20)
    mid = BASE_BY_AGE_PAISE[age_band] * pct // 100
    low = mid * (100 - RANGE_SPREAD_PCT) // 100 // 10_000 * 10_000
    high = mid * (100 + RANGE_SPREAD_PCT) // 100 // 10_000 * 10_000
    return Quote(low_paise=low, high_paise=high)

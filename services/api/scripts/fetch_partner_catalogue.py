"""Refresh data/partners/budli/phones.json from the partner's public products.json (phones only).
Run: python scripts/fetch_partner_catalogue.py   (needs network; commit the snapshot)."""

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.partners.catalogue import PACKAGED, SNAPSHOT, parse_product, slim  # noqa: E402

BASE = "https://buy.budli.in/products.json?limit=250&page={}"


def main() -> None:
    out = []
    for page in range(1, 30):
        with urllib.request.urlopen(BASE.format(page), timeout=60) as r:  # noqa: S310
            batch = json.load(r)["products"]
        if not batch:
            break
        out += [slim(p) for p in batch if parse_product(p)]
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(out, indent=0, sort_keys=True) + "\n")
    PACKAGED.write_text(SNAPSHOT.read_text())
    print(f"wrote {len(out)} phones to {SNAPSHOT}")


if __name__ == "__main__":
    main()

"""Re-encrypt every device IMEI under the newest IMEI_ENCRYPTION_KEYS entry (see docs/SECURITY.md).

Usage: uv run python scripts/rotate_imei_keys.py [--dry-run]
Prepend the new key to IMEI_ENCRYPTION_KEYS first (old keys stay until this finishes). Idempotent.
"""

import sys

from sqlalchemy import select

from app.core.db import _session_factory
from app.inventory.imei import decrypt_imei, rotate_imei
from app.inventory.models import Device


def main(dry_run: bool) -> int:
    changed = 0
    with _session_factory()() as db:
        for d in db.scalars(select(Device)):
            decrypt_imei(d.imei_encrypted)  # fails loudly if no configured key can read it
            new = rotate_imei(d.imei_encrypted)
            if not dry_run:
                d.imei_encrypted = new
            changed += 1
        if not dry_run:
            db.commit()
    print(f"{'would re-encrypt' if dry_run else 're-encrypted'} {changed} device IMEIs")
    return 0


if __name__ == "__main__":
    sys.exit(main("--dry-run" in sys.argv))

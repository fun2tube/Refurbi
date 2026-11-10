"""Shipments adapter. Fake courier in dev/preview; a real courier plugs in here."""

import secrets
from typing import Protocol


class Courier(Protocol):
    def create_shipment(self, order_number: str, pincode: str) -> dict: ...


class FakeCourier:
    def create_shipment(self, order_number: str, pincode: str) -> dict:
        return {"carrier": "DEMO-COURIER", "tracking_no": f"DEMO{secrets.token_hex(5).upper()}"}


def get_courier() -> Courier:
    return FakeCourier()

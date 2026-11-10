"""Payment gateway adapter: Razorpay in prod, fake in dev/tests/preview (no real keys in repo)."""

import base64
import hashlib
import hmac
import json
import secrets
import urllib.request
from typing import Protocol

from app.core.settings import get_settings


def sign(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def verify_signature(body: bytes, signature: str | None) -> bool:
    s = get_settings()
    if not signature:
        return False
    if s.razorpay_webhook_secret.startswith("dev-only") and s.app_env not in (
        "dev",
        "preview",
        "test",
    ):
        return False  # never accept webhooks signed with the public dev secret in production
    return hmac.compare_digest(sign(body, s.razorpay_webhook_secret), signature)


class Gateway(Protocol):
    name: str

    def create_order(self, amount_paise: int, receipt: str) -> dict: ...

    def refund(self, payment_id: str | None, amount_paise: int) -> str: ...


class FakeGateway:
    name = "fake"

    def create_order(self, amount_paise: int, receipt: str) -> dict:
        return {"order_id": f"fake_order_{secrets.token_hex(8)}", "key_id": "fake_key"}

    def refund(self, payment_id: str | None, amount_paise: int) -> str:
        return f"fake_refund_{secrets.token_hex(6)}"


class RazorpayGateway:
    name = "razorpay"

    def create_order(self, amount_paise: int, receipt: str) -> dict:
        s = get_settings()
        auth = base64.b64encode(f"{s.razorpay_key_id}:{s.razorpay_key_secret}".encode()).decode()
        req = urllib.request.Request(
            "https://api.razorpay.com/v1/orders",
            data=json.dumps(
                {"amount": amount_paise, "currency": "INR", "receipt": receipt[:40]}
            ).encode(),
            headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:  # noqa: S310 - fixed https URL
            return {"order_id": json.load(r)["id"], "key_id": s.razorpay_key_id}

    def refund(self, payment_id: str | None, amount_paise: int) -> str:
        s = get_settings()
        auth = base64.b64encode(f"{s.razorpay_key_id}:{s.razorpay_key_secret}".encode()).decode()
        req = urllib.request.Request(
            f"https://api.razorpay.com/v1/payments/{payment_id}/refund",
            data=json.dumps({"amount": amount_paise}).encode(),
            headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:  # noqa: S310 - fixed https URL
            return json.load(r)["id"]


def get_gateway() -> Gateway:
    s = get_settings()
    return RazorpayGateway() if s.razorpay_key_id and s.razorpay_key_secret else FakeGateway()

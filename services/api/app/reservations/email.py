"""Email adapter (Brevo free tier in prod; fake outbox in dev/tests). Never real keys in repo."""

import json
import logging
import urllib.request
from typing import Protocol

from app.core.settings import get_settings

log = logging.getLogger("refurbi.email")


class EmailSender(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...


class FakeEmailSender:
    outbox: list[dict] = []

    def send(self, to: str, subject: str, body: str) -> None:
        self.outbox.append({"to": to, "subject": subject, "body": body})
        log.info("fake email queued", extra={"subject": subject})  # no recipient/body in logs


class BrevoEmailSender:
    def send(self, to: str, subject: str, body: str) -> None:
        s = get_settings()
        payload = {
            "sender": {"email": s.email_from, "name": "Refurbi"},
            "to": [{"email": to}],
            "subject": subject,
            "textContent": body,
        }
        req = urllib.request.Request(
            "https://api.brevo.com/v3/smtp/email",
            data=json.dumps(payload).encode(),
            headers={"api-key": s.brevo_api_key, "content-type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10).close()  # noqa: S310 - fixed https URL


def get_email_sender() -> EmailSender:
    if get_settings().brevo_api_key:
        return BrevoEmailSender()
    return FakeEmailSender()

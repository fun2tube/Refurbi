"""IMEI blacklist check adapter. Dev/test uses a deterministic fake; a real CEIR/paid lookup
can be added later behind the same interface (no key needed to build)."""

from typing import Protocol

from app.procurement.models import ImeiResult

FAKE_BLOCKED_PREFIX = "13579"  # fake adapter: IMEIs starting with this are "blacklisted"


class ImeiChecker(Protocol):
    name: str

    def check(self, imei: str) -> ImeiResult: ...


class FakeImeiChecker:
    name = "fake"

    def check(self, imei: str) -> ImeiResult:
        return ImeiResult.BLOCKED if imei.startswith(FAKE_BLOCKED_PREFIX) else ImeiResult.CLEAR


def get_imei_checker() -> ImeiChecker:
    return FakeImeiChecker()

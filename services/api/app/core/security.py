"""Security hardening helpers (T34): response headers and a small in-memory login throttle."""

from collections import defaultdict, deque
from time import monotonic

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import AppError

_HEADERS = {
    b"x-content-type-options": b"nosniff",
    b"x-frame-options": b"DENY",
    b"referrer-policy": b"strict-origin-when-cross-origin",
    b"permissions-policy": b"camera=(), microphone=(), geolocation=()",
    b"cross-origin-resource-policy": b"cross-origin",  # web app on another origin loads /media
}


class SecurityHeadersMiddleware:
    """Pure ASGI (no body buffering). HSTS only when `hsts` is set (never in dev/test)."""

    def __init__(self, app: ASGIApp, hsts: bool = False) -> None:
        self.app = app
        self.hsts = hsts

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        no_store = scope["path"].startswith(("/auth", "/admin", "/pos", "/partner"))

        async def wrapped(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                present = {k.lower() for k, _ in headers}
                for k, v in _HEADERS.items():
                    if k not in present:
                        headers.append((k, v))
                if self.hsts and b"strict-transport-security" not in present:
                    headers.append((b"strict-transport-security", b"max-age=31536000"))
                if no_store and b"cache-control" not in present:
                    headers.append((b"cache-control", b"no-store"))
            await send(message)

        await self.app(scope, receive, wrapped)


class TooManyAttempts(AppError):
    status_code = 429
    code = "rate_limited"


class AttemptLimiter:
    """Sliding-window counter per key. In-memory (per process): fine for one small API instance;
    move to a shared store if the API is scaled out."""

    def __init__(self, limit: int, window_s: int) -> None:
        self.limit, self.window_s = limit, window_s
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def _prune(self, key: str) -> deque[float]:
        q = self._hits[key]
        now = monotonic()
        while q and q[0] < now - self.window_s:
            q.popleft()
        return q

    def check(self, key: str) -> None:
        """Raise if `key` already used up its failures in the window (does not record)."""
        if len(self._prune(key)) >= self.limit:
            raise TooManyAttempts("Too many attempts. Please wait a few minutes and try again.")

    def fail(self, key: str) -> None:
        self._prune(key).append(monotonic())

    def clear(self, key: str) -> None:
        self._hits.pop(key, None)

    def reset(self) -> None:
        self._hits.clear()

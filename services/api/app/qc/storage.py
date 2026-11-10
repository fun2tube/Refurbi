"""Image storage adapter. Dev/tests: local disk. Production (free tier): Cloudflare R2 via its
S3-compatible API (SigV4 PUT, stdlib only). Select with STORAGE_BACKEND=local|s3."""

import hashlib
import hmac
import pathlib
import urllib.request
from datetime import UTC, datetime
from typing import Protocol

from app.core.settings import get_settings


class Storage(Protocol):
    def put(self, key: str, data: bytes, content_type: str) -> str:
        """Store bytes, return the public URL."""


class LocalStorage:
    def __init__(self, root: str, public_prefix: str = "/media"):
        self.root, self.prefix = pathlib.Path(root), public_prefix

    def put(self, key: str, data: bytes, content_type: str) -> str:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return f"{self.prefix}/{key}"


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


class S3Storage:
    """Minimal S3-compatible uploader (Cloudflare R2: region 'auto')."""

    def __init__(self, endpoint, bucket, access_key, secret_key, public_base, region="auto"):
        self.endpoint, self.bucket = endpoint.rstrip("/"), bucket
        self.ak, self.sk, self.public_base, self.region = (
            access_key,
            secret_key,
            public_base,
            region,
        )

    def build_request(self, key: str, data: bytes, content_type: str, now: datetime | None = None):
        now = now or datetime.now(UTC)
        amz, day = now.strftime("%Y%m%dT%H%M%SZ"), now.strftime("%Y%m%d")
        host = self.endpoint.split("://", 1)[1]
        path = f"/{self.bucket}/{key}"
        payload_hash = hashlib.sha256(data).hexdigest()
        headers = {"content-type": content_type, "host": host,
                   "x-amz-content-sha256": payload_hash, "x-amz-date": amz}  # fmt: skip
        signed = ";".join(sorted(headers))
        canon = "\n".join(
            [
                "PUT",
                path,
                "",
                *(f"{k}:{headers[k]}" for k in sorted(headers)),
                "",
                signed,
                payload_hash,
            ]
        )
        scope = f"{day}/{self.region}/s3/aws4_request"
        to_sign = "\n".join(
            ["AWS4-HMAC-SHA256", amz, scope, hashlib.sha256(canon.encode()).hexdigest()]
        )
        k = _sign(
            _sign(_sign(_sign(("AWS4" + self.sk).encode(), day), self.region), "s3"), "aws4_request"
        )
        sig = hmac.new(k, to_sign.encode(), hashlib.sha256).hexdigest()
        auth = (
            f"AWS4-HMAC-SHA256 Credential={self.ak}/{scope}, "
            f"SignedHeaders={signed}, Signature={sig}"
        )
        req = urllib.request.Request(self.endpoint + path, data=data, method="PUT")
        for h, v in headers.items():
            if h != "host":
                req.add_header(h, v)
        req.add_header("Authorization", auth)
        return req

    def put(self, key: str, data: bytes, content_type: str) -> str:
        with urllib.request.urlopen(self.build_request(key, data, content_type), timeout=20):
            pass
        return f"{self.public_base.rstrip('/')}/{key}"


def get_storage() -> Storage:
    s = get_settings()
    if s.storage_backend == "s3":
        return S3Storage(
            s.s3_endpoint, s.s3_bucket, s.s3_access_key, s.s3_secret_key, s.s3_public_base
        )
    return LocalStorage(s.media_dir)

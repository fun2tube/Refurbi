import hashlib
import pathlib

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.auth.deps import require_permission
from app.auth.models import User
from app.catalog.models import ProductModel, ProductVariant
from app.core.db import get_session
from app.core.errors import AppError, NotFoundError
from app.core.settings import get_settings
from app.inventory.lifecycle import transition
from app.inventory.models import (
    Device,
    DevicePhoto,
    DeviceStatus,
    DeviceTest,
    Grade,
)
from app.qc.storage import Storage, get_storage
from app.qc.template import RESULTS, SMARTPHONE_TEMPLATE

router = APIRouter(prefix="/admin/qc", tags=["qc-admin"])
media = APIRouter(tags=["media"])
_perm = Depends(require_permission("inventory.write"))

MAX_PHOTO_BYTES = 5 * 1024 * 1024
MAX_PHOTOS = 12
_MAGIC = [(b"\xff\xd8\xff", "image/jpeg", "jpg"), (b"\x89PNG\r\n\x1a\n", "image/png", "png")]


def _sniff(data: bytes) -> tuple[str, str] | None:
    for magic, ctype, ext in _MAGIC:
        if data.startswith(magic):
            return ctype, ext
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp", "webp"
    return None


class QCIn(BaseModel):
    checklist: dict[str, str]
    battery_health: int = Field(ge=0, le=100)
    grade: str | None = None
    notes: str = ""


def _device(db: Session, device_id: int) -> Device:
    d = db.get(Device, device_id)
    if d is None:
        raise NotFoundError("Device not found")
    return d


@router.get("/template")
def template(_: User = _perm):
    return {
        "category": "smartphone",
        "results": list(RESULTS),
        "items": [i._asdict() for i in SMARTPHONE_TEMPLATE],
    }


@router.post("/devices/{device_id}/tests", status_code=201)
def submit_qc(device_id: int, body: QCIn, db: Session = Depends(get_session), user: User = _perm):
    d = _device(db, device_id)
    keys = {i.key for i in SMARTPHONE_TEMPLATE}
    if set(body.checklist) != keys:
        raise AppError("Checklist must contain every template item", code="invalid_checklist",
                       details={"missing": sorted(keys - set(body.checklist)),
                                "unknown": sorted(set(body.checklist) - keys)})  # fmt: skip
    if any(v not in RESULTS for v in body.checklist.values()):
        raise AppError("Checklist results must be pass, fail or na", code="invalid_checklist")
    failed = [i.key for i in SMARTPHONE_TEMPLATE if i.critical and body.checklist[i.key] != "pass"]
    passed = not failed
    if passed and body.grade not in {g.value for g in Grade}:
        raise AppError("A grade (A/B/C) is required to pass QC", code="grade_required")
    if d.status != DeviceStatus.QC_PENDING.value:
        transition(db, d.id, DeviceStatus.QC_PENDING, actor_user_id=user.id, reason="QC started")
    db.execute(
        update(DeviceTest)
        .where(DeviceTest.device_id == d.id, DeviceTest.is_current.is_(True))
        .values(is_current=False)
    )
    db.flush()
    db.add(
        DeviceTest(
            device_id=d.id,
            checklist={"results": body.checklist, "notes": body.notes},
            passed=passed,
            is_current=True,
            tested_by=user.id,
        )
    )
    d.battery_health = body.battery_health
    d.grade = body.grade if passed else None
    db.flush()
    if passed:
        transition(db, d.id, DeviceStatus.QC_PASSED, actor_user_id=user.id, reason="QC passed")
    else:
        transition(db, d.id, DeviceStatus.QC_FAILED, actor_user_id=user.id,
                   reason=("QC failed: " + ", ".join(failed))[:255])  # fmt: skip
    db.commit()
    return {"device_id": d.id, "passed": passed, "failed_items": failed, "status": d.status,
            "grade": d.grade}  # fmt: skip


@router.put("/devices/{device_id}/photos", status_code=201)
async def upload_photo(
    device_id: int,
    request: Request,
    kind: str = "cosmetic",
    db: Session = Depends(get_session),
    storage: Storage = Depends(get_storage),
    _: User = _perm,
):
    """Raw image body (Content-Type image/jpeg|png|webp), max 5 MB, magic bytes verified."""
    d = _device(db, device_id)
    data = await request.body()
    if not data or len(data) > MAX_PHOTO_BYTES:
        raise AppError("Photo must be between 1 byte and 5 MB", code="invalid_photo")
    sniffed = _sniff(data)
    if sniffed is None:
        raise AppError("Only JPEG, PNG or WebP images are accepted", code="invalid_photo")
    count = len(db.scalars(select(DevicePhoto.id).where(DevicePhoto.device_id == d.id)).all())
    if count >= MAX_PHOTOS:
        raise AppError(f"At most {MAX_PHOTOS} photos per device", code="too_many_photos")
    ctype, ext = sniffed
    key = f"devices/{d.id}/{hashlib.sha256(data).hexdigest()[:16]}.{ext}"
    photo = DevicePhoto(device_id=d.id, url=storage.put(key, data, ctype), kind=kind[:30],
                        sort_order=count)  # fmt: skip
    db.add(photo)
    db.commit()
    return {"id": photo.id, "url": photo.url, "kind": photo.kind}


@router.delete("/devices/{device_id}/photos/{photo_id}", status_code=204)
def delete_photo(
    device_id: int, photo_id: int, db: Session = Depends(get_session), _: User = _perm
):
    p = db.get(DevicePhoto, photo_id)
    if p is None or p.device_id != device_id:
        raise NotFoundError("Photo not found")
    db.delete(p)
    db.commit()


@router.get("/devices/{device_id}/certificate")
def certificate(device_id: int, db: Session = Depends(get_session), _: User = _perm):
    """Data for the QC certificate (rendered by the UI/PDF later). Only IMEI last 4 digits."""
    d = _device(db, device_id)
    t = db.scalar(
        select(DeviceTest).where(DeviceTest.device_id == d.id, DeviceTest.is_current.is_(True))
    )
    if t is None:
        raise NotFoundError("No QC test recorded for this device")
    v = db.get(ProductVariant, d.variant_id)
    m = db.get(ProductModel, v.model_id)
    results = t.checklist.get("results", {})
    return {
        "device_id": d.id,
        "model": m.name,
        "storage_gb": v.storage_gb,
        "imei_last4": d.imei_last4,
        "grade": d.grade,
        "battery_health": d.battery_health,
        "passed": t.passed,
        "tested_at": t.tested_at,
        "items": [
            {"label": i.label, "result": results.get(i.key), "critical": i.critical}
            for i in SMARTPHONE_TEMPLATE
        ],
        "notes": t.checklist.get("notes", ""),
    }


@media.get("/media/{path:path}")
def serve_media(path: str):
    """Serves locally stored device photos in dev/preview (R2 serves them in production)."""
    root = pathlib.Path(get_settings().media_dir).resolve()
    f = (root / path).resolve()
    if not f.is_relative_to(root) or not f.is_file() or f.suffix not in {".jpg", ".png", ".webp"}:
        raise NotFoundError("Not found")
    return FileResponse(f)

"""Idempotent seed: permissions, roles, and the super admin from env.

Run: uv run python -m app.seed (set SUPER_ADMIN_EMAIL and SUPER_ADMIN_PASSWORD for the admin)
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import Permission, Role, User, UserRole
from app.auth.rbac import PERMISSIONS, ROLES
from app.auth.security import hash_password
from app.catalog.seed import seed_catalog
from app.core.settings import get_settings
from app.preview_seed import seed_preview


def seed_rbac(db: Session) -> None:
    perms = {p.code: p for p in db.scalars(select(Permission))}
    for code, desc in PERMISSIONS.items():
        if code not in perms:
            perms[code] = Permission(code=code, description=desc)
            db.add(perms[code])
    roles = {r.code: r for r in db.scalars(select(Role))}
    for code, (name, perm_codes) in ROLES.items():
        role = roles.get(code) or Role(code=code, name=name)
        role.name = name
        role.permissions = [perms[c] for c in perm_codes]
        db.add(role)
    db.commit()


def seed_super_admin(db: Session, email: str, password: str) -> User | None:
    if not email or not password:
        return None
    email = email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, password_hash=hash_password(password), full_name="Super Admin")
        db.add(user)
        db.flush()
    role = db.scalar(select(Role).where(Role.code == "super_admin"))
    exists = db.scalar(
        select(UserRole.id).where(
            UserRole.user_id == user.id,
            UserRole.role_id == role.id,
            UserRole.counter_id.is_(None),
        )
    )
    if role and not exists:
        db.add(UserRole(user_id=user.id, role_id=role.id, counter_id=None))
    db.commit()
    return user


def main() -> None:
    from app.core.db import _session_factory

    s = get_settings()
    with _session_factory()() as db:
        seed_rbac(db)
        seed_catalog(db)
        admin = seed_super_admin(db, s.super_admin_email, s.super_admin_password)
        if s.is_preview:
            print("preview demo data:", seed_preview(db))
        print("seeded rbac;", "super admin ready" if admin else "super admin skipped (env not set)")


if __name__ == "__main__":
    main()

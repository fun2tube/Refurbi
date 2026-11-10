"""Auth tables. counter_id on user_roles is a plain integer until the counters table lands (T14)."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

ID = BigInteger().with_variant(Integer, "sqlite")


class Permission(Base):
    __tablename__ = "permissions"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    code: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(String(255), default="")


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    permissions: Mapped[list[Permission]] = relationship(
        secondary="role_permissions", lazy="selectin"
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_id: Mapped[int] = mapped_column(ID, ForeignKey("roles.id"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ID, ForeignKey("permissions.id"), primary_key=True)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(150), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    roles: Mapped[list["UserRole"]] = relationship(lazy="selectin")


class UserRole(Base):
    """A role granted to a user, optionally scoped to one counter (NULL = global)."""

    __tablename__ = "user_roles"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    user_id: Mapped[int] = mapped_column(ID, ForeignKey("users.id"))
    role_id: Mapped[int] = mapped_column(ID, ForeignKey("roles.id"))
    counter_id: Mapped[int | None] = mapped_column(ID, nullable=True)
    role: Mapped[Role] = relationship(lazy="selectin")

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", "counter_id", name="uq_user_roles_scope"),
        Index("ix_user_roles_user_id", "user_id"),
    )


class RefreshToken(Base):
    """Rotating refresh token (SHA-256 hash only); family_id enables reuse detection."""

    __tablename__ = "refresh_tokens"
    id: Mapped[int] = mapped_column(ID, primary_key=True)
    user_id: Mapped[int] = mapped_column(ID, ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    family_id: Mapped[str] = mapped_column(String(36), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

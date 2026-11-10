"""Import all ORM models here so Alembic autogenerate sees them."""

from app.auth import models as auth_models  # noqa: F401
from app.core.db import Base  # noqa: F401

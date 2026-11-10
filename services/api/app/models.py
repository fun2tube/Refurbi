"""Import all ORM models here so Alembic autogenerate sees them."""

from app.auth import models as auth_models  # noqa: F401
from app.catalog import models as catalog_models  # noqa: F401
from app.core.db import Base  # noqa: F401
from app.inventory import models as inventory_models  # noqa: F401

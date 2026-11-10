"""Import all ORM models here so Alembic autogenerate sees them."""

from app.auth import models as auth_models  # noqa: F401
from app.billing import models as billing_models  # noqa: F401
from app.catalog import models as catalog_models  # noqa: F401
from app.core.db import Base  # noqa: F401
from app.counters import models as counters_models  # noqa: F401
from app.exchange import models as exchange_models  # noqa: F401
from app.inventory import models as inventory_models  # noqa: F401
from app.pos import models as pos_models  # noqa: F401
from app.pricing import models as pricing_models  # noqa: F401
from app.procurement import models as procurement_models  # noqa: F401
from app.transfers import models as transfers_models  # noqa: F401

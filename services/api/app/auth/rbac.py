"""Permission catalogue and default roles (seeded by app.seed)."""

PERMISSIONS: dict[str, str] = {
    "users.manage": "Create and manage staff/partner users",
    "catalog.read": "View catalogue in admin",
    "catalog.write": "Edit catalogue",
    "inventory.read": "View devices and stock",
    "inventory.write": "Add/edit devices, run QC",
    "pricing.write": "Change device prices",
    "counters.manage": "Manage counters, agreements and commission rules",
    "transfers.manage": "Create, approve and receive stock transfers",
    "transfers.receive": "Confirm receipt of a transfer at own counter",
    "leads.manage": "View and manage exchange enquiries",
    "procurement.write": "Suppliers, purchase orders, goods receipt",
    "counter.stock.read": "View stock at a counter",
    "counter.sell": "Sell a device at a counter (POS)",
    "sales.read": "View sales and invoices",
    "warranty.manage": "Manage warranty claims",
    "commission.read": "View commission statements",
}

ROLES: dict[str, tuple[str, list[str]]] = {
    "super_admin": ("Super admin", list(PERMISSIONS)),
    "admin": ("Admin", [p for p in PERMISSIONS if p != "users.manage"]),
    "qc_technician": ("QC technician", ["inventory.read", "inventory.write"]),
    "counter_partner": (
        "Counter partner",
        [
            "counter.stock.read",
            "counter.sell",
            "sales.read",
            "commission.read",
            "transfers.receive",
        ],
    ),
}

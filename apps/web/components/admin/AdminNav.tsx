import Link from "next/link";

export const ADMIN_LINKS = [
  { href: "/admin", label: "Dashboard" },
  { href: "/admin/inventory", label: "Inventory" },
  { href: "/admin/receive", label: "Receive stock" },
  { href: "/admin/exchange", label: "Exchange enquiries" },
  { href: "/admin/warranty", label: "Warranty claims" },
  { href: "/admin/commissions", label: "Commission" },
  { href: "/admin/login", label: "Sign in" },
];

export function AdminNav() {
  return (
    <nav className="mt-4 space-y-1 text-sm">
      {ADMIN_LINKS.map((l) => (
        <Link key={l.href} href={l.href} className="block rounded px-2 py-1 hover:bg-white/10">
          {l.label}
        </Link>
      ))}
    </nav>
  );
}

import Link from "next/link";
import { Card } from "@/components/ui";

export default function Page() {
  const tiles = [
    { href: "/admin/inventory", t: "Inventory", d: "All devices: filter by brand, model, status, grade, battery, location, age." },
    { href: "/admin/receive", t: "Receive stock", d: "Suppliers, purchase orders and goods receipt (IMEI check on every unit)." },
    { href: "/admin/login", t: "Sign in", d: "Demo admin sign-in." },
  ];
  return (
    <div className="space-y-4">
      <h1 className="font-display text-2xl font-bold">Admin</h1>
      <div className="grid gap-3 sm:grid-cols-2">
        {tiles.map((x) => (
          <Link key={x.href} href={x.href}>
            <Card className="h-full space-y-1 hover:opacity-90">
              <div className="font-display font-semibold">{x.t}</div>
              <div className="text-sm text-midnight/70">{x.d}</div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}

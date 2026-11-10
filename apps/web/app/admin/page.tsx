import Link from "next/link";

export default function Page() {
  return (
    <div className="space-y-3">
      <h1 className="font-display text-2xl font-bold">Admin</h1>
      <p className="text-midnight/70">Inventory, QC and pricing screens are coming soon.</p>
      <Link href="/admin/login" className="text-brand underline">
        Sign in
      </Link>
    </div>
  );
}

import Link from "next/link";
import type { ReactNode } from "react";

export function StoreShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="border-b border-silver/40 bg-porcelain">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Link href="/" className="font-display text-xl font-bold lowercase">
            refurbi<span className="text-brand">.</span>
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
    </div>
  );
}

function SidebarShell({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="min-h-screen md:grid md:grid-cols-[220px_1fr]">
      <aside className="bg-midnight p-4 text-porcelain">
        <div className="font-display text-lg font-bold lowercase">
          refurbi<span className="text-brand">.</span>
        </div>
        <div className="mt-1 text-xs uppercase tracking-wide text-silver">{title}</div>
      </aside>
      <main className="p-6">{children}</main>
    </div>
  );
}

export const AdminShell = ({ children }: { children: ReactNode }) => (
  <SidebarShell title="Admin">{children}</SidebarShell>
);
export const PartnerShell = ({ children }: { children: ReactNode }) => (
  <SidebarShell title="Partner">{children}</SidebarShell>
);

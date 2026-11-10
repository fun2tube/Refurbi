import { BottomNav } from "./store/BottomNav";
import { Footer } from "./store/Footer";
import { Header } from "./store/Header";
import type { ReactNode } from "react";

export function StoreShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <Header />
      <main>{children}</main>
      <Footer />
      <BottomNav />
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

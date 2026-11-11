"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { m } from "motion/react";
import { cn } from "@/lib/cn";
import { spring } from "@/lib/motion";

const ITEMS = [
  { href: "/", label: "Home", d: "M3 11l9-8 9 8v9a1 1 0 01-1 1h-5v-6H9v6H4a1 1 0 01-1-1z" },
  { href: "/refurbished-mobiles", label: "Phones", d: "M8 2h8a2 2 0 012 2v16a2 2 0 01-2 2H8a2 2 0 01-2-2V4a2 2 0 012-2zm4 17h.01" },
  { href: "/stores", label: "Stores", d: "M12 21s-7-6.2-7-11a7 7 0 0114 0c0 4.8-7 11-7 11zm0-8.5a2.5 2.5 0 100-5 2.5 2.5 0 000 5z" },
  { href: "/exchange", label: "Exchange", d: "M7 7h11l-3-3m3 13H7l3 3" },
  { href: "/quality-check", label: "Trust", d: "M12 3l8 3v6c0 4.5-3.2 8-8 9-4.8-1-8-4.5-8-9V6zm-3 9l2 2 4-4" },
];

export function BottomNav() {
  const path = usePathname();
  return (
    <nav
      aria-label="Quick navigation"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-silver/40 bg-porcelain/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden"
    >
      <ul className="grid grid-cols-5">
        {ITEMS.map((i) => {
          const active = i.href === "/" ? path === "/" : path.startsWith(i.href);
          return (
            <li key={i.href}>
              <Link
                href={i.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "relative flex min-h-[52px] flex-col items-center justify-center gap-0.5 py-2 text-[11px] font-medium",
                  active ? "text-brand" : "text-midnight/70",
                )}
              >
                {active && (
                  <m.span
                    layoutId="nav-pill"
                    aria-hidden
                    className="absolute inset-x-2 inset-y-1 rounded-2xl bg-brand/10"
                    transition={spring.snappy}
                  />
                )}
                <svg viewBox="0 0 24 24" className="relative h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                  <path d={i.d} />
                </svg>
                <span className="relative">{i.label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

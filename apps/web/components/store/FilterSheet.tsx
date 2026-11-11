"use client";
import { AnimatePresence, m } from "motion/react";
import { useEffect, useState } from "react";
import { spring } from "@/lib/motion";

/**
 * Filters: always inline from md up; on phones a "Filters" button opens a spring bottom sheet holding the same form.
 * Without JS the form is shown inline (see noscript style), so filtering never depends on motion.
 */
export function FilterSheet({ children, activeCount = 0 }: { children: React.ReactNode; activeCount?: number }) {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);
  return (
    <div className="mt-5">
      <noscript>
        <style>{".filter-inline{display:block!important}.filter-btn{display:none!important}"}</style>
      </noscript>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-haspopup="dialog"
        className="filter-btn inline-flex h-11 items-center gap-2 rounded-full border border-silver bg-white px-5 text-sm font-medium md:hidden"
      >
        Filters{activeCount > 0 && <span className="rounded-full bg-brand px-2 text-xs text-white">{activeCount}</span>}
      </button>
      {/* desktop: inline form */}
      <div className="filter-inline hidden md:block">{!open && children}</div>
      <AnimatePresence>
        {open && (
          <div className="fixed inset-0 z-50 md:hidden" role="dialog" aria-modal="true" aria-label="Filters">
            <m.div
              className="absolute inset-0 bg-midnight/60"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setOpen(false)}
            />
            <m.div
              className="absolute inset-x-0 bottom-0 max-h-[85svh] overflow-y-auto rounded-t-3xl bg-porcelain p-4 pb-24"
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={spring.sheet}
            >
              <div className="mb-3 flex items-center justify-between">
                <h2 className="font-display text-lg font-bold">Filters</h2>
                <button type="button" onClick={() => setOpen(false)} className="h-11 px-3 text-sm font-medium text-brand">
                  Close
                </button>
              </div>
              {children}
            </m.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

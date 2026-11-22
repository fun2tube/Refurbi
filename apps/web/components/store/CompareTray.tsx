"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { AnimatePresence, m } from "motion/react";
import { cheapestId, clearCompare, readCompare, removeCompare, type CompareItem, MAX_COMPARE } from "@/lib/compare";
import { formatRupees } from "@/lib/money";

const rows: [string, (c: CompareItem) => string][] = [
  ["Price", (c) => formatRupees(c.price_paise)],
  ["Grade", (c) => (c.grade ? `Grade ${c.grade}` : "—")],
  ["Storage", (c) => `${c.storage_gb} GB`],
  ["RAM", (c) => (c.ram_gb ? `${c.ram_gb} GB` : "—")],
  ["Battery", (c) => (c.battery_health != null ? `${c.battery_health}%` : "Tested")],
  ["Available at", (c) => c.store ?? "Warehouse"],
];

export function CompareTray() {
  const [items, setItems] = useState<CompareItem[]>([]);
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const sync = () => setItems(readCompare());
    sync();
    window.addEventListener("refurbi-compare", sync);
    return () => window.removeEventListener("refurbi-compare", sync);
  }, []);
  useEffect(() => {
    if (!open) return;
    const k = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [open]);
  useEffect(() => {
    if (items.length < 2) setOpen(false);
  }, [items.length]);

  const best = cheapestId(items);
  return (
    <>
      <AnimatePresence>
        {items.length > 0 && (
          <m.div
            initial={{ y: 80, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 80, opacity: 0 }}
            transition={{ type: "spring", stiffness: 380, damping: 32 }}
            className="fixed inset-x-2 bottom-[calc(4.5rem+env(safe-area-inset-bottom))] z-40 mx-auto flex max-w-xl items-center gap-2 rounded-2xl border border-silver/50 bg-white p-2 shadow-lg md:bottom-4"
            role="region"
            aria-label="Compare phones"
          >
            <ul className="flex flex-1 gap-2">
              {items.map((c) => (
                <li key={c.id} className="relative">
                  <div className="flex h-11 w-11 items-center justify-center overflow-hidden rounded-lg bg-porcelain text-[10px] font-semibold" title={c.name}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    {c.photo ? <img src={c.photo} alt={c.name} className="h-full object-contain" /> : c.brand.slice(0, 3)}
                  </div>
                  <button type="button" aria-label={`Remove ${c.name}`} onClick={() => removeCompare(c.id)} className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-midnight text-xs text-white">×</button>
                </li>
              ))}
              {items.length < MAX_COMPARE && <li className="flex items-center text-xs text-midnight/60">Add {items.length < 2 ? "one more" : "up to 3"}</li>}
            </ul>
            <button type="button" disabled={items.length < 2} onClick={() => setOpen(true)} className="h-11 rounded-xl bg-brand px-4 text-sm font-semibold text-white disabled:opacity-40">
              Compare
            </button>
          </m.div>
        )}
      </AnimatePresence>
      <AnimatePresence>
        {open && items.length >= 2 && (
          <m.div className="fixed inset-0 z-50 flex items-end justify-center bg-midnight/50 md:items-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setOpen(false)}>
            <m.div
              role="dialog" aria-modal="true" aria-label="Compare phones"
              initial={{ y: 60 }} animate={{ y: 0 }} exit={{ y: 60 }} transition={{ type: "spring", stiffness: 380, damping: 34 }}
              onClick={(e) => e.stopPropagation()}
              className="max-h-[85vh] w-full max-w-2xl overflow-auto rounded-t-3xl bg-white p-4 md:rounded-3xl"
            >
              <div className="flex items-center justify-between">
                <h2 className="font-display text-lg font-bold">Compare</h2>
                <button type="button" autoFocus onClick={() => setOpen(false)} className="h-11 rounded-lg px-3 text-sm font-medium">Close</button>
              </div>
              <table className="mt-2 w-full table-fixed text-left text-sm">
                <thead>
                  <tr>
                    <th className="w-20" />
                    {items.map((c) => (
                      <th key={c.id} scope="col" className="p-1 align-top text-xs font-semibold">
                        <Link href={`/refurbished-${c.slug}`} onClick={() => setOpen(false)} className="underline-offset-2 hover:underline">{c.name}</Link>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map(([label, fn]) => (
                    <tr key={label} className="border-t border-silver/30">
                      <th scope="row" className="py-2 pr-1 text-xs font-medium text-midnight/60">{label}</th>
                      {items.map((c) => (
                        <td key={c.id} className={`p-1 ${label === "Price" && c.id === best ? "font-bold text-brand-dark" : ""}`}>
                          {fn(c)}{label === "Price" && c.id === best ? " · lowest" : ""}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              <button type="button" onClick={() => { clearCompare(); setOpen(false); }} className="mt-3 h-11 text-sm font-medium text-midnight/70 underline">Clear all</button>
            </m.div>
          </m.div>
        )}
      </AnimatePresence>
    </>
  );
}

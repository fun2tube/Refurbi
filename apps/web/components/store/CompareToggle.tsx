"use client";
import { useEffect, useState } from "react";
import type { Unit } from "@/lib/api";
import { readCompare, toCompareItem, toggleCompare } from "@/lib/compare";

/** Small 44px "Compare" control that sits over a listing card (outside the card link). */
export function CompareToggle({ unit }: { unit: Unit }) {
  const [on, setOn] = useState(false);
  const [full, setFull] = useState(false);
  useEffect(() => {
    const sync = () => setOn(readCompare().some((c) => c.id === unit.unit_id));
    sync();
    window.addEventListener("refurbi-compare", sync);
    return () => window.removeEventListener("refurbi-compare", sync);
  }, [unit.unit_id]);
  return (
    <button
      type="button"
      aria-pressed={on}
      aria-label={`Compare ${unit.model.name} ${unit.storage_gb}GB`}
      onClick={() => setFull(toggleCompare(toCompareItem(unit)) === "full")}
      className={`absolute right-1 top-1 flex h-11 min-w-11 items-center justify-center rounded-full px-3 text-xs font-semibold backdrop-blur transition-colors ${
        on ? "bg-brand text-white" : "bg-white/85 text-midnight hover:bg-white"
      }`}
    >
      {full ? "Max 3" : on ? "✓ Added" : "Compare"}
    </button>
  );
}

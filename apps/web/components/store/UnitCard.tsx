import Link from "next/link";
import { GradeBadge, Price } from "@/components/ui";
import type { Unit } from "@/lib/api";
import { TapCard } from "@/components/motion/TapCard";
import { RevealItem } from "@/components/product/ClipReveal";
import { DeviceArt } from "./DeviceArt";

export function unitTitle(u: Unit): string {
  return `${u.model.name} ${u.storage_gb}GB`;
}

export function UnitCard({ unit }: { unit: Unit }) {
  return (
    <Link
      href={`/refurbished-${unit.model.slug}`}
      className="group flex flex-col overflow-hidden rounded-2xl border border-silver/40 bg-white transition-shadow hover:shadow-md"
    >
      <div className="relative flex h-44 items-center justify-center bg-gradient-to-b from-porcelain to-silver/20 py-4 sm:h-52">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        {unit.photos[0] ? <img src={unit.photos[0]} alt={unitTitle(unit)} className="h-full object-contain" /> : (
          <DeviceArt seed={unit.unit_id} className="transition-transform duration-300 group-hover:-translate-y-1" />
        )}
        {unit.grade && <GradeBadge grade={unit.grade} className="absolute left-3 top-3" />}
      </div>
      <div className="flex flex-1 flex-col gap-1 p-3 sm:p-4">
        <div className="text-[11px] font-medium uppercase tracking-wide text-midnight/60">{unit.model.brand.name}</div>
        <h3 className="font-display text-sm font-semibold leading-snug sm:text-base">{unitTitle(unit)}</h3>
        <p className="text-xs text-midnight/65">
          {unit.battery_health != null ? `Battery ${unit.battery_health}%` : "Battery tested"}
          {unit.store ? ` · ${unit.store.name}` : " · Ships from warehouse"}
        </p>
        <Price paise={unit.price_paise} className="mt-auto pt-2 text-lg" />
      </div>
    </Link>
  );
}

export function UnitGrid({ units }: { units: Unit[] }) {
  return (
    <ul className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
      {units.map((u, i) => (
        <RevealItem key={u.unit_id} index={i % 4}>
          <TapCard>
            <UnitCard unit={u} />
          </TapCard>
        </RevealItem>
      ))}
    </ul>
  );
}

"use client";
import { m } from "motion/react";
import { useState } from "react";
import { DeviceArt } from "@/components/store/DeviceArt";
import { spring } from "@/lib/motion";

/** 3D card-flip gallery: front = phone, back = quick facts. Button toggles (keyboard + touch). */
export function FlipGallery({ seed, name, facts, photos = [] }: { seed: number; name: string; facts: string[]; photos?: string[] }) {
  const [back, setBack] = useState(false);
  const [i, setI] = useState(0);
  const shown = photos[i];
  return (
    <div className="relative h-72 md:h-[28rem] [perspective:1000px]">
      <m.div
        className="relative h-full w-full [transform-style:preserve-3d]"
        initial={false}
        animate={{ rotateY: back ? 180 : 0 }}
        transition={spring.soft}
      >
        <div className="absolute inset-0 flex items-center justify-center rounded-3xl bg-gradient-to-b from-white to-silver/25 py-6 [backface-visibility:hidden]">
          {shown ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={shown} alt={name} className="h-full w-full object-contain" loading="eager" decoding="async" />
          ) : (
            <DeviceArt seed={seed} label={`${name} illustration`} />
          )}
        </div>
        <div className="absolute inset-0 flex flex-col justify-center gap-3 rounded-3xl bg-midnight p-8 text-porcelain [backface-visibility:hidden] [transform:rotateY(180deg)]">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-silver">At a glance</p>
          <ul className="space-y-2 font-display text-lg">
            {facts.map((f) => (
              <li key={f}>✓ {f}</li>
            ))}
          </ul>
        </div>
      </m.div>
      {photos.length > 1 && !back && (
        <div className="absolute bottom-3 left-3 flex gap-2">
          {photos.slice(0, 4).map((u, n) => (
            <button
              key={u}
              type="button"
              onClick={() => setI(n)}
              aria-label={`Photo ${n + 1}`}
              aria-pressed={n === i}
              className={`h-11 w-11 overflow-hidden rounded-lg border-2 bg-white ${n === i ? "border-midnight" : "border-transparent"}`}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={u} alt="" className="h-full w-full object-cover" loading="lazy" />
            </button>
          ))}
        </div>
      )}
      <button
        type="button"
        onClick={() => setBack((b) => !b)}
        aria-pressed={back}
        className="absolute bottom-3 right-3 inline-flex h-11 items-center rounded-full bg-midnight/80 px-4 text-sm font-medium text-porcelain backdrop-blur"
      >
        {back ? "Show phone" : "At a glance"}
      </button>
    </div>
  );
}

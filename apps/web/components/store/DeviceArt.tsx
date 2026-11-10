import { cn } from "@/lib/cn";

/** Generic placeholder phone silhouette (no brand marks). Tone varies per seed for visual rhythm. */
const TONES = [
  ["#1b1f27", "#2c3340"],
  ["#2b3a36", "#3d524b"],
  ["#3a4350", "#59636f"],
  ["#d9dde1", "#eef0f2"],
];

export function DeviceArt({
  seed = 0,
  className,
  label = "Phone illustration",
}: {
  seed?: number;
  className?: string;
  label?: string;
}) {
  const [a, b] = TONES[Math.abs(seed) % TONES.length];
  const id = `g${Math.abs(seed) % TONES.length}`;
  const light = Math.abs(seed) % TONES.length === 3;
  return (
    <svg
      viewBox="0 0 120 200"
      role="img"
      aria-label={label}
      className={cn("h-full w-auto drop-shadow-[0_18px_24px_rgba(17,19,24,0.25)]", className)}
    >
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor={b} />
          <stop offset="1" stopColor={a} />
        </linearGradient>
      </defs>
      <rect x="10" y="4" width="100" height="192" rx="18" fill={light ? "#a8b1b9" : "#0b0d10"} />
      <rect x="14" y="8" width="92" height="184" rx="14" fill={`url(#${id})`} />
      <rect x="44" y="14" width="32" height="7" rx="3.5" fill={light ? "#a8b1b9" : "#0b0d10"} opacity="0.85" />
      <circle cx="60" cy="108" r="22" fill="none" stroke="#247c65" strokeOpacity="0.55" strokeWidth="2" />
      <path d="M50 108l7 7 14-15" fill="none" stroke="#247c65" strokeOpacity="0.9" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

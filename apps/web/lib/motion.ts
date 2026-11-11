/** Motion design tokens (see docs/DESIGN_MOTION.md). Pure data: safe to import anywhere. */
export const duration = { fast: 0.18, base: 0.35, slow: 0.7, scene: 1.2 } as const;

export const ease = {
  out: [0.22, 1, 0.36, 1],
  inOut: [0.65, 0, 0.35, 1],
  curtain: [0.76, 0, 0.24, 1],
} as const;

export const spring = {
  snappy: { type: "spring", stiffness: 420, damping: 34 },
  soft: { type: "spring", stiffness: 180, damping: 24 },
  sheet: { type: "spring", stiffness: 300, damping: 32 },
} as const;

/** Stagger delay for the i-th item, capped so long lists never feel slow. */
export const stagger = (i: number, step = 0.06, max = 0.5) => Math.min(i * step, max);

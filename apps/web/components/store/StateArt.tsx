/** Animated empty / error illustrations (stroke draw via CSS, calm under reduced motion). */
export function StateArt({ kind }: { kind: "empty" | "error" }) {
  return (
    <svg viewBox="0 0 64 64" aria-hidden className="mx-auto mb-3 h-16 w-16 text-brand" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="18" y="6" width="28" height="52" rx="6" className="draw" pathLength={1} />
      {kind === "empty" ? <path d="M26 30h12M32 24v12" className="draw" pathLength={1} /> : <path d="M26 24l12 12M38 24L26 36" className="draw" pathLength={1} />}
    </svg>
  );
}

# Refurbi cinematic design: concept, storyboard, tokens, guardrails

Status: founder request 2026-11-11. A founder brief or Figma export placed in `docs/design/` overrides this file.

## Concept: "Second life, first class"
Every phone is inspected, restored and reborn. The store plays like a short film (dark, dramatic scenes) cut with
bright, calm shopping sections (Porcelain) where buying is effortless. Drama never blocks the path to Buy/Reserve.

## Storyboard
| # | Scene | Surface | Motion |
|---|-------|---------|--------|
| 0 | Intro (first visit only, <=1.2s, tap to skip) | Midnight | `refurbi.` draws in (SVG stroke), dot pulses green |
| 1 | Hero | Midnight + green glow | Phone rises from darkness with rim light, slow 3D rotate on scroll, light sweep across screen, word-by-word headline |
| 2 | Reborn (pinned) | Midnight | Phone morphs worn -> restored as you scroll (scratches fade, glow rises); draggable before/after fallback |
| 3 | Inspected | Midnight | Exploded layers; checkpoint markers draw in (battery, screen, camera, ports); battery bar fills |
| 4 | Brands / budgets | Porcelain | Swipeable 3D-tilted cards |
| 5 | Available now | Porcelain | Cards stagger in, spotlight follows finger, tap squash |
| 6 | Trust stats | Midnight | Count-up numbers |
| 7 | Stores | Porcelain | Animated map pins; magnetic WhatsApp button |
| P | Product | Porcelain/Midnight | layoutId flight from card, 3D card-flip gallery, unit reveal (flip to grade + battery ring + price count-up), clip-path spec reveals, sticky Reserve bar, green burst + checkmark draw on success |
| L | Listing/flows | Porcelain | Bottom-sheet filters (spring), chip morph, grid FLIP, compare tray dock, swipeable step cards, animated empty/error SVGs |

Route changes use a ~350ms brand-green curtain wipe.

## Tokens (code: `lib/motion.ts`, CSS: `app/globals.css`)
- Colour: Midnight #111318, Porcelain #F7F7F5, Silver #A8B1B9, Green #247C65 (glow `--glow`). Grain overlay `.film-grain`.
- Type: Manrope (display, kinetic), Inter (UI).
- Durations: fast 0.18s, base 0.35s, slow 0.7s, scene 1.2s.
- Easing: `out` [0.22,1,0.36,1], `inOut` [0.65,0,0.35,1], `curtain` [0.76,0,0.24,1].
- Springs: `snappy` (stiffness 420, damping 34), `soft` (180/24), `sheet` (300/32).

## Tech
`motion` (`motion/react`) with `LazyMotion` + `domAnimation` and `m.*` components (keeps initial JS small; heavy scenes loaded with
`next/dynamic` below the fold). Scroll scenes: `useScroll`/`useTransform`/`useSpring`, sticky pinned sections. Shared elements: `layoutId`.
3D via CSS transforms and layered SVG/PNG parallax (no WebGL/three.js). Android `navigator.vibrate` for key moments only.

## Guardrails (non-negotiable)
- Animate `transform`, `opacity`, `clip-path` only.
- `prefers-reduced-motion`: calm, instant version (`useReducedMotionSafe`; `MotionConfig reducedMotion="user"`).
- Content and Buy/Reserve buttons usable immediately: no blocking intro; intro <=1.2s, first visit, tap to skip.
- LCP <=2.5s on mid-range Android, CLS <=0.1, INP <=200ms; motion JS <= ~60 KB gzip; touch targets >=44px; WCAG AA contrast.
- Design at 360-430px first; test at 375px.
- No claims like "Apple certified" or "100% original parts" in copy.

## Audit log (TP10, local production build, Lighthouse 12 mobile preset, seeded demo API)
| Page | Perf | A11y | Best practices | CLS | TBT | LCP (simulated slow 4G + 4x CPU) |
|------|------|------|----------------|-----|-----|-----|
| Home | 90 | 100 | 100 | 0 | 160 ms | 3.3 s |
| Listing | 88 | 100 | 100 | 0 | 250 ms | 3.3 s |
| Product | 92 | 100 | 100 | 0 | 120 ms | 3.2 s |
- Real (unthrottled, localhost) LCP is 0.2 s; the simulated figure is above the 2.5 s target and must be re-measured against the Render deploy (network + cold start dominate there). Shared JS stays 103 kB; motion adds no shared-bundle weight (heavy scenes are client components below the fold).
- Open follow-ups: chip morph, compare tray, swipeable checkout step cards, layoutId card->page flight (needs same-document transition).

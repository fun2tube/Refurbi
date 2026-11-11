/** Word-by-word headline. Pure CSS animation (no JS), text is in the HTML for SEO and LCP. */
export function HeroHeadline({ text }: { text: string }) {
  return (
    <h1 className="mt-3 font-display text-4xl font-bold leading-tight md:text-5xl" aria-label={text}>
      {text.split(" ").map((w, i) => (
        <span key={i} aria-hidden className="word-in" style={{ animationDelay: `${0.1 + i * 0.07}s` }}>
          {w}
          {" "}
        </span>
      ))}
    </h1>
  );
}

import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { Skeleton, CardGridSkeleton } from "../ui/Skeleton";
import { INTRO_MS } from "./IntroSplash";

describe("TP6B motion pieces", () => {
  it("intro is capped at 1.2s", () => expect(INTRO_MS).toBeLessThanOrEqual(1200));
  it("skeleton uses shimmer utility and is hidden from AT", () => {
    const html = renderToString(<Skeleton className="h-4" />);
    expect(html).toContain("shimmer");
    expect(html).toContain('aria-hidden="true"');
  });
  it("grid skeleton renders requested count", () => {
    expect(renderToString(<CardGridSkeleton count={3} />).match(/aspect-\[4\/5\]/g)).toHaveLength(3);
  });
});

import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { HeroHeadline } from "./HeroHeadline";
import { RebornScene } from "./RebornScene";

describe("TP7A home scenes", () => {
  it("headline keeps full text for SEO/AT and animates per word", () => {
    const html = renderToString(<HeroHeadline text="Checked and graded." />);
    expect(html).toContain('aria-label="Checked and graded."');
    expect(html.match(/word-in/g)).toHaveLength(3);
  });
  it("reborn scene SSRs in calm mode with a before/after slider and no unverified claims", () => {
    const html = renderToString(<RebornScene />);
    expect(html).toContain('type="range"');
    expect(html.toLowerCase()).not.toMatch(/certified|100% original/);
  });
});

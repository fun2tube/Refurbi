import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { FlipGallery } from "./FlipGallery";
import { BatteryRing } from "./BatteryRing";

describe("TP8 product reveal", () => {
  it("flip gallery is a pressable toggle with both faces in the DOM", () => {
    const html = renderToString(<FlipGallery seed={1} name="Test Phone" facts={["5G", "Battery health shown"]} />);
    expect(html).toContain('aria-pressed="false"');
    expect(html).toContain("Battery health shown");
    expect(html.toLowerCase()).not.toMatch(/certified|100% original/);
  });
  it("battery ring exposes the real percentage to assistive tech and clamps", () => {
    expect(renderToString(<BatteryRing percent={87} />)).toContain("Battery health 87%");
    expect(renderToString(<BatteryRing percent={140} />)).toContain("Battery health 100%");
  });
});

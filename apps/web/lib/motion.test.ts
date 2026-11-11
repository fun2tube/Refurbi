import { expect, it } from "vitest";
import { duration, ease, spring, stagger } from "./motion";

it("tokens are sane and the intro budget holds", () => {
  expect(duration.scene).toBeLessThanOrEqual(1.2);
  expect(ease.out).toHaveLength(4);
  expect(spring.sheet.type).toBe("spring");
});

it("stagger is capped", () => {
  expect(stagger(2)).toBeCloseTo(0.12);
  expect(stagger(100)).toBe(0.5);
});

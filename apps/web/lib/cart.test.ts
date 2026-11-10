import { describe, expect, it } from "vitest";
import { parseCart } from "./cart";

describe("parseCart", () => {
  it("handles junk", () => {
    expect(parseCart(null)).toEqual([]);
    expect(parseCart("{bad")).toEqual([]);
    expect(parseCart('{"a":1}')).toEqual([]);
  });
  it("dedupes, filters and caps at 5", () => {
    expect(parseCart("[1,1,2,-3,\"x\",4.5]")).toEqual([1, 2]);
    expect(parseCart("[1,2,3,4,5,6,7]")).toEqual([1, 2, 3, 4, 5]);
  });
});

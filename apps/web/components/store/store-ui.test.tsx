import { describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { FilterSheet } from "./FilterSheet";
import { StateArt } from "./StateArt";

describe("TP9 listing UI", () => {
  it("filter form stays in the HTML (works without JS) and sheet trigger is a 44px button", () => {
    const html = renderToString(
      <FilterSheet activeCount={2}>
        <form action="/x"><input name="q" /></form>
      </FilterSheet>,
    );
    expect(html).toContain('name="q"');
    expect(html).toContain("h-11");
    expect(html).toContain(">2<");
    expect(html).toContain("filter-inline");
  });
  it("state art is decorative", () => {
    expect(renderToString(<StateArt kind="empty" />)).toContain('aria-hidden="true"');
  });
});

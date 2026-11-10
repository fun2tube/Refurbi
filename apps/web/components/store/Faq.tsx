export type FaqItem = { q: string; a: string };

export function Faq({ items, id = "faq" }: { items: FaqItem[]; id?: string }) {
  return (
    <section aria-labelledby={id}>
      <h2 id={id} className="font-display text-xl font-bold">
        Questions
      </h2>
      <div className="mt-3 divide-y divide-silver/40 rounded-2xl border border-silver/40 bg-white">
        {items.map((f) => (
          <details key={f.q} className="group p-4">
            <summary className="cursor-pointer list-none font-medium marker:hidden">
              <span className="mr-2 text-brand">+</span>
              {f.q}
            </summary>
            <p className="mt-2 text-sm text-midnight/75">{f.a}</p>
          </details>
        ))}
      </div>
    </section>
  );
}

export const PRODUCT_FAQS: FaqItem[] = [
  { q: "What do the grades mean?", a: "Grade A, B and C describe the cosmetic condition of the phone. Grade A is the cleanest. See the grading page for details." },
  { q: "Why is battery health shown?", a: "Battery health is measured on the exact phone you are buying, so you know how it holds up before you pay." },
  { q: "Is the phone new?", a: "No. These are pre-owned phones that have been checked and, where needed, repaired before listing." },
  { q: "Can I see the phone before buying?", a: "Yes. Most units are at a store near you; choose Visit store to see where each unit is." },
  { q: "What about warranty and returns?", a: "Warranty and return terms are explained on our warranty and returns pages, and apply as stated on your invoice." },
];

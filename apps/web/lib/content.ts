/** Trust-page content. Plain TS so it builds without an MDX toolchain; swap for MDX files later.
 *  RULE: no invented business facts. Anything the founder must confirm is marked TBC here and listed
 *  in PROGRESS.md (grade definitions, warranty months, return window, addresses, contacts). */
export type Section = { h: string; p?: string[]; list?: string[] };
export type FaqItem = { q: string; a: string };
export type ContentPage = { slug: string; title: string; description: string; intro: string; sections: Section[]; faqs?: FaqItem[] };

const TBC = "To be confirmed before launch.";

export const PAGES: ContentPage[] = [
  {
    slug: "quality-check",
    title: "How we check every phone",
    description: "Each refurbished phone is tested device by device and its results are recorded before it is listed.",
    intro: "A phone is only listed after it has been tested. The result of the test is attached to that exact phone.",
    sections: [
      { h: "What we look at", list: ["Identity: the phone's IMEI is verified and recorded", "Battery: health percentage is measured and shown on the listing", "Screen, touch, cameras, speakers, microphones, buttons and ports", "Network, Wi-Fi, Bluetooth and charging", "Cosmetic condition, which sets the grade"] },
      { h: "What you see", p: ["On every listing you can see the grade, the measured battery health and the store holding the phone."] },
      { h: "If a phone fails", p: ["Phones that fail a check are repaired and re-tested, or are not sold."] },
    ],
  },
  {
    slug: "grading",
    title: "Grading",
    description: "What Grade A, B and C mean for the cosmetic condition of a refurbished phone.",
    intro: "Grades describe how a phone looks. Every graded phone has passed the same functional checks.",
    sections: [
      { h: "Grade A", p: ["The cleanest condition. Little or no visible signs of use."] },
      { h: "Grade B", p: ["Light signs of use such as minor scratches or small marks on the body or frame."] },
      { h: "Grade C", p: ["Clearly visible signs of use. Works the same, priced lower."] },
      { h: "Good to know", p: [`These descriptions are indicative while final grade standards are being confirmed. ${TBC}`] },
    ],
  },
  {
    slug: "warranty",
    title: "Warranty",
    description: "How warranty works on a Refurbi phone.",
    intro: "Every phone comes with an invoice. Warranty terms are shown on the invoice you receive.",
    sections: [
      { h: "Warranty period", p: [`The warranty period for each grade is ${TBC.toLowerCase()}`] },
      { h: "What is covered", p: [`Coverage and exclusions are ${TBC.toLowerCase()}`] },
      { h: "How to claim", p: ["Contact the store you bought from, or message us, with your invoice number and phone number."] },
    ],
  },
  {
    slug: "returns",
    title: "Returns",
    description: "Return policy for refurbished phones.",
    intro: "We want you to be happy with the phone you buy.",
    sections: [
      { h: "Return window", p: [`The return window and conditions are ${TBC.toLowerCase()}`] },
      { h: "How to start a return", p: ["Contact the store you bought from, or message us, with your invoice."] },
    ],
  },
  {
    slug: "about",
    title: "About Refurbi",
    description: "Refurbi sells checked and graded refurbished smartphones through stores near you.",
    intro: "Refurbi helps people buy a good phone for less, with the details laid out clearly.",
    sections: [
      { h: "What we do", p: ["We list real, individually tested phones with grade, battery health and price, and hold them at stores where you can see them."] },
      { h: "Company details", p: [`Registered business details will be published here. ${TBC}`] },
    ],
  },
  {
    slug: "contact",
    title: "Contact us",
    description: "Contact Refurbi by WhatsApp or visit a store.",
    intro: "The fastest way to reach us is WhatsApp. Or visit a store.",
    sections: [
      { h: "Phone and email", p: [`Contact numbers and email are ${TBC.toLowerCase()}`] },
      { h: "Visit a store", p: ["See the store list for where phones are in stock."] },
    ],
  },
  {
    slug: "faq",
    title: "Frequently asked questions",
    description: "Answers about refurbished phones, grades, battery health, warranty and buying from Refurbi.",
    intro: "Short answers to common questions.",
    sections: [],
    faqs: [
      { q: "What is a refurbished phone?", a: "A pre-owned phone that has been tested, cleaned and, where needed, repaired before being sold again. It is not a new phone." },
      { q: "What do Grade A, B and C mean?", a: "They describe cosmetic condition only. See the grading page." },
      { q: "How is battery health measured?", a: "We read it from the phone during testing and show it on that phone's listing." },
      { q: "Do I get an invoice?", a: "Yes, every phone is sold with an invoice." },
      { q: "What is the warranty?", a: "Warranty terms are shown on your invoice and explained on the warranty page." },
      { q: "Can I return a phone?", a: "Return terms are explained on the returns page." },
      { q: "Can I see a phone before I buy?", a: "Yes. Pick a phone held at a store and visit." },
      { q: "Can I exchange my old phone?", a: "An exchange option is planned. Message us on WhatsApp in the meantime." },
    ],
  },
];

export const bySlug = (slug: string) => PAGES.find((p) => p.slug === slug);

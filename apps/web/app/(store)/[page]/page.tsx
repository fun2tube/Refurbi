import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Container } from "@/components/store/Container";
import { Faq } from "@/components/store/Faq";
import { WhatsAppButton } from "@/components/store/WhatsAppButton";
import { PAGES, bySlug } from "@/lib/content";

export const dynamicParams = false;
export function generateStaticParams() {
  return PAGES.map((p) => ({ page: p.slug }));
}

type Props = { params: Promise<{ page: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const p = bySlug((await params).page);
  if (!p) return {};
  return { title: p.title, description: p.description, alternates: { canonical: `/${p.slug}` } };
}

export default async function TrustPage({ params }: Props) {
  const p = bySlug((await params).page);
  if (!p) notFound();
  const faqLd = p.faqs && {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: p.faqs.map((f) => ({ "@type": "Question", name: f.q, acceptedAnswer: { "@type": "Answer", text: f.a } })),
  };
  return (
    <Container className="max-w-3xl py-8 md:py-12">
      {faqLd && <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(faqLd) }} />}
      <h1 className="font-display text-3xl font-bold">{p.title}</h1>
      <p className="mt-2 text-midnight/75">{p.intro}</p>
      <div className="mt-8 space-y-8">
        {p.sections.map((s) => (
          <section key={s.h}>
            <h2 className="font-display text-xl font-semibold">{s.h}</h2>
            {s.p?.map((t) => (
              <p key={t} className="mt-2 text-midnight/80">{t}</p>
            ))}
            {s.list && (
              <ul className="mt-2 list-disc space-y-1 pl-5 text-midnight/80">
                {s.list.map((t) => <li key={t}>{t}</li>)}
              </ul>
            )}
          </section>
        ))}
        {p.faqs && <Faq items={p.faqs} />}
      </div>
      <div className="mt-10 flex flex-wrap gap-3">
        <WhatsAppButton message={`Hi Refurbi, I have a question about: ${p.title}`} label="Ask us on WhatsApp" />
        <Link href="/refurbished-mobiles" className="inline-flex h-12 items-center rounded-full border border-silver px-6 font-medium">
          Browse phones
        </Link>
      </div>
    </Container>
  );
}

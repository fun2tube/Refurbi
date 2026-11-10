"use client";
import { useEffect, useState } from "react";
import Script from "next/script";
import { usePathname } from "next/navigation";
import { useReportWebVitals } from "next/web-vitals";
import { cfBeaconToken, events, gaId, readConsent, track, vitalsParams, writeConsent, type Consent } from "@/lib/analytics";

/** Consent banner + GA4 (after consent) + Cloudflare Web Analytics (cookieless) + WhatsApp click tracking. */
export function Analytics() {
  const ga = gaId();
  const cf = cfBeaconToken();
  const path = usePathname();
  const [consent, setConsent] = useState<Consent | null | undefined>(undefined);

  useEffect(() => {
    const sync = () => setConsent(readConsent());
    sync();
    window.addEventListener("refurbi-consent", sync);
    return () => window.removeEventListener("refurbi-consent", sync);
  }, []);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      const a = (e.target as Element | null)?.closest?.("a[href^='https://wa.me']");
      if (a) track("whatsapp_click", events.whatsappClick(window.location.pathname));
    };
    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, []);

  useReportWebVitals((m) => track("web_vitals", vitalsParams(m)));

  useEffect(() => {
    if (ga && consent === "granted") track("page_view", { page_path: path });
  }, [ga, consent, path]);

  return (
    <>
      {cf && <Script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon={JSON.stringify({ token: cf })} strategy="afterInteractive" />}
      {ga && consent === "granted" && (
        <>
          <Script src={`https://www.googletagmanager.com/gtag/js?id=${ga}`} strategy="afterInteractive" />
          <Script id="ga4-init" strategy="afterInteractive">{`window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}window.gtag=gtag;gtag('js',new Date());gtag('config','${ga}',{send_page_view:false,anonymize_ip:true});`}</Script>
        </>
      )}
      {ga && consent === null && (
        <div role="dialog" aria-label="Analytics consent" className="fixed inset-x-3 bottom-20 z-50 rounded-xl border border-silver/40 bg-white p-4 text-sm shadow-lg md:bottom-4 md:left-auto md:max-w-sm">
          <p>We use Google Analytics, only if you agree, to see which pages help. No personal details are sent.</p>
          <div className="mt-3 flex gap-2">
            <button type="button" className="h-9 rounded-full bg-brand px-4 text-white" onClick={() => writeConsent("granted")}>Accept</button>
            <button type="button" className="h-9 rounded-full border border-silver px-4" onClick={() => writeConsent("denied")}>No thanks</button>
          </div>
        </div>
      )}
    </>
  );
}

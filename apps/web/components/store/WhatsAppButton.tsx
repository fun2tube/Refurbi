import { cn } from "@/lib/cn";
import { hasRealWhatsapp, whatsappLink } from "@/lib/site";

export function WhatsAppButton({
  message,
  label = "Chat on WhatsApp",
  className,
}: {
  message: string;
  label?: string;
  className?: string;
}) {
  return (
    <a
      href={whatsappLink(message)}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        "inline-flex h-12 items-center justify-center gap-2 rounded-full bg-brand px-6 text-base font-medium text-white hover:bg-brand-dark",
        className,
      )}
    >
      {label}
      {!hasRealWhatsapp() && <span className="rounded bg-white/20 px-1.5 text-[10px] uppercase">demo number</span>}
    </a>
  );
}

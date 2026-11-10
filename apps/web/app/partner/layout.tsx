import { PartnerShell } from "@/components/shells";

export default function Layout({ children }: { children: React.ReactNode }) {
  return <PartnerShell>{children}</PartnerShell>;
}

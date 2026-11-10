import { StoreShell } from "@/components/shells";

export default function Layout({ children }: { children: React.ReactNode }) {
  return <StoreShell>{children}</StoreShell>;
}

import { Container } from "@/components/store/Container";
import { PreviewMap } from "@/components/store/PreviewMap";

export const metadata = { title: "Preview map", robots: { index: false } };

export default function PreviewPage() {
  return (
    <Container className="py-8">
      <PreviewMap />
    </Container>
  );
}

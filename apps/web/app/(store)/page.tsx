import { Button, Card, GradeBadge, Price } from "@/components/ui";

// Placeholder page showing the design system; real homepage is T21. Demo values only.
export default function Home() {
  return (
    <div className="space-y-6">
      <h1 className="font-display text-3xl font-bold">Refurbished phones, checked and graded.</h1>
      <Card className="max-w-sm space-y-2">
        <GradeBadge grade="A" />
        <div className="text-sm text-midnight/70">Demo device</div>
        <Price paise={2499900} strikePaise={3499900} className="text-xl" />
        <Button>Reserve</Button>
      </Card>
    </div>
  );
}

import { cn } from "@/lib/cn";

/** Grade labels are placeholders until the founder confirms grade definitions. */
export type Grade = "A" | "B" | "C";

const styles: Record<Grade, string> = {
  A: "bg-brand/10 text-brand-dark",
  B: "bg-silver/25 text-midnight",
  C: "bg-midnight/10 text-midnight",
};

export function GradeBadge({ grade, className }: { grade: Grade; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold",
        styles[grade],
        className,
      )}
    >
      Grade {grade}
    </span>
  );
}

import { cn } from "@/lib/cn";

/** Shimmering placeholder block (CSS-only; calm under reduced motion). */
export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden className={cn("shimmer rounded-xl", className)} />;
}

export function CardGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div role="status" aria-label="Loading" className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="aspect-[4/5] w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/3" />
        </div>
      ))}
    </div>
  );
}

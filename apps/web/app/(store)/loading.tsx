import { CardGridSkeleton, Skeleton } from "@/components/ui/Skeleton";

export default function Loading() {
  return (
    <div className="mx-auto max-w-6xl space-y-4 px-4 py-6">
      <Skeleton className="h-8 w-1/2" />
      <CardGridSkeleton />
    </div>
  );
}

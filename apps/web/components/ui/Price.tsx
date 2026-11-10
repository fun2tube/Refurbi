import { cn } from "@/lib/cn";
import { formatRupees } from "@/lib/money";

export function Price({
  paise,
  strikePaise,
  className,
}: {
  paise: number;
  strikePaise?: number;
  className?: string;
}) {
  return (
    <span className={cn("font-display tabular-nums font-semibold", className)}>
      {formatRupees(paise)}
      {strikePaise ? (
        <s className="ml-2 text-sm font-normal text-silver">{formatRupees(strikePaise)}</s>
      ) : null}
    </span>
  );
}

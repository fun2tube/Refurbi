"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { StateArt } from "./StateArt";

/** Friendly failure state for server-fetched data. While the API is waking up it re-checks every 8s. */
export function ApiError({ error, waking }: { error: string; waking?: boolean }) {
  const router = useRouter();
  useEffect(() => {
    if (!waking) return;
    const id = setInterval(() => router.refresh(), 8000);
    return () => clearInterval(id);
  }, [waking, router]);
  return (
    <div role="status" className="rounded-2xl border border-midnight/10 bg-white p-5 text-sm text-midnight/80">
      {waking && (
        <span aria-hidden className="mb-3 block h-1.5 w-24 animate-pulse rounded-full bg-brand" />
      )}
      {!waking && <StateArt kind="error" />}
      <p className="font-medium">{waking ? "Waking up" : "Something went wrong"}</p>
      <p className="mt-1 text-midnight/70">{error}</p>
      {waking && <p className="mt-1 text-midnight/70">This page will refresh by itself.</p>}
    </div>
  );
}

"use client";
import { ApiError } from "@/components/store/ApiError";

/** Last-resort boundary: a page that throws shows a friendly retry instead of a crash. */
export default function Error({ reset }: { error: Error; reset: () => void }) {
  return (
    <div className="mx-auto w-full max-w-xl px-4 py-16">
      <ApiError error="This page hit a problem. Please try again." />
      <button type="button" onClick={reset} className="mt-4 h-11 rounded-full bg-brand px-6 text-sm font-medium text-white">
        Try again
      </button>
    </div>
  );
}

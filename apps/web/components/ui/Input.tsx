import type { InputHTMLAttributes, SelectHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

const field =
  "h-10 w-full rounded-lg border border-silver bg-white px-3 text-sm text-midnight " +
  "placeholder:text-silver focus-visible:outline-2 focus-visible:outline-brand";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn(field, className)} {...props} />;
}

export function Select({ className, children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select className={cn(field, className)} {...props}>
      {children}
    </select>
  );
}

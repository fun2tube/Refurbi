"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { readCart } from "@/lib/cart";

export function CartLink() {
  const [n, setN] = useState(0);
  useEffect(() => {
    const sync = () => setN(readCart().length);
    sync();
    window.addEventListener("refurbi-cart", sync);
    return () => window.removeEventListener("refurbi-cart", sync);
  }, []);
  return (
    <Link href="/cart" className="shrink-0 text-sm font-medium text-midnight/80 hover:text-brand" aria-label={`Cart, ${n} items`}>
      Cart{n > 0 ? ` (${n})` : ""}
    </Link>
  );
}

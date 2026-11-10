"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { addToCart, readCart } from "@/lib/cart";
import { events, track } from "@/lib/analytics";

export function AddToCart({ unitId }: { unitId: number }) {
  const [inCart, setInCart] = useState(false);
  const [full, setFull] = useState(false);
  useEffect(() => {
    const sync = () => setInCart(readCart().includes(unitId));
    sync();
    window.addEventListener("refurbi-cart", sync);
    return () => window.removeEventListener("refurbi-cart", sync);
  }, [unitId]);
  if (inCart)
    return (
      <Link href="/cart" className="inline-flex h-10 items-center rounded-full border border-brand px-4 text-sm font-medium text-brand">
        In cart - view cart
      </Link>
    );
  return (
    <>
      <button
        type="button"
        onClick={() => { const ok = addToCart(unitId); setFull(!ok); if (ok) track("add_to_cart", events.addToCart(unitId)); }}
        className="inline-flex h-10 items-center rounded-full bg-midnight px-4 text-sm font-medium text-white hover:bg-midnight/90"
      >
        Add to cart
      </button>
      {full && <span role="alert" className="text-xs text-red-700">Cart is full (max 5 phones).</span>}
    </>
  );
}

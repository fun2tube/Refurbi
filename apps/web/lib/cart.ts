/** Browser cart: only unit ids are stored; prices/availability are re-checked by the API. */
const KEY = "refurbi.cart.v1";
export const MAX_CART = 5;

export function parseCart(raw: string | null): number[] {
  try {
    const v = JSON.parse(raw ?? "[]");
    if (!Array.isArray(v)) return [];
    return [...new Set(v.filter((x): x is number => Number.isInteger(x) && x > 0))].slice(0, MAX_CART);
  } catch {
    return [];
  }
}

export function readCart(): number[] {
  try {
    return parseCart(localStorage.getItem(KEY));
  } catch {
    return [];
  }
}

export function writeCart(ids: number[]): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(ids.slice(0, MAX_CART)));
    window.dispatchEvent(new Event("refurbi-cart"));
  } catch {
    /* storage unavailable: cart simply does not persist */
  }
}

export function addToCart(id: number): boolean {
  const c = readCart();
  if (c.includes(id)) return true;
  if (c.length >= MAX_CART) return false;
  writeCart([...c, id]);
  return true;
}

export function removeFromCart(id: number): void {
  writeCart(readCart().filter((x) => x !== id));
}

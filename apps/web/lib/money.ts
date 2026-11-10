/** Money is integer paise everywhere. Format only at the edge. */
export function formatRupees(paise: number): string {
  if (!Number.isInteger(paise)) throw new Error("paise must be an integer");
  const negative = paise < 0;
  const abs = Math.abs(paise);
  const rupees = Math.floor(abs / 100);
  const rem = abs % 100;
  // Indian digit grouping: last three digits, then groups of two.
  const s = String(rupees);
  const grouped =
    s.length > 3
      ? s.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ",") + "," + s.slice(-3)
      : s;
  const frac = rem ? "." + String(rem).padStart(2, "0") : "";
  return `${negative ? "-" : ""}₹${grouped}${frac}`;
}

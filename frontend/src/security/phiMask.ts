/**
 * PHI display-mask helpers.
 *
 * These functions render patient identifiers in the UI as default-masked values
 * with a click-to-reveal fallback. Real PHI never leaves the backend.
 */
export function phiMask(text: string, marker = "[PHI] "): string {
  if (!text) return text;
  return marker + "••••";
}

export function tryDisplay<T extends string>(value: T, revealed: boolean): T {
  return revealed ? value : (("••••" as unknown) as T);
}

export function maskMRN(mrn: string): string {
  if (!mrn) return "";
  if (mrn.length < 4) return "••••";
  return "••••" + mrn.slice(-4);
}

export function maskSSN(ssn: string): string {
  if (!ssn || ssn.length < 4) return "••••";
  return "•••-••-" + ssn.slice(-4);
}

/**
 * Audit emit – client-side attribution of high-impact user actions.
 *
 * Sends a non-PII audit beacon to the API so the server-side audit chain
 * captures who initiated an action (login, decrypt-button click, etc.).
 */
export async function auditEmit(action: string, target?: string, payload?: Record<string, unknown>) {
  try {
    await fetch("/v1/__audit/emit", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, target, payload }),
    });
  } catch (err) {
    // Never block UI on audit emission failure.
    console.warn("audit emit failed", err);
  }
}

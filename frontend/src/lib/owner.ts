const STORAGE_KEY = "lumina_owner";

/**
 * A random token identifying this browser to the API, so sessions and their
 * documents are visible only here. It is not an account and not an identity —
 * it never leaves this device except as a request header, and clearing site
 * data discards it (along with access to anything created under it).
 */
let cached: string | null = null;

function generate(): string {
  // randomUUID needs a secure context; plain http:// on a LAN IP is not one,
  // which is exactly how this gets opened during local testing.
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

export function ownerToken(): string {
  if (cached) return cached;
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      cached = stored;
      return stored;
    }
    cached = generate();
    localStorage.setItem(STORAGE_KEY, cached);
  } catch {
    // Storage blocked (Safari private mode, embedded webviews). Keep a
    // process-lifetime token so the app still works; it just will not survive
    // a reload, which degrades to the pre-ownership behaviour rather than
    // erroring.
    cached = cached || generate();
  }
  return cached;
}

/** Header sent on every API call. */
export function ownerHeaders(): Record<string, string> {
  return { "X-Owner-Token": ownerToken() };
}

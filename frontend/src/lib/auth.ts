/**
 * Session-token storage for Google sign-in.
 *
 * The token is a short-lived JWT the API issues after Google confirms identity.
 * It lives in localStorage and rides on `Authorization: Bearer` — not a cookie —
 * because the SPA (vercel.app) and API (hf.space) are different sites and
 * third-party cookies are unreliable. Signing out is just dropping the key.
 */
const JWT_KEY = "lumina_jwt";

export function getToken(): string | null {
  try {
    return localStorage.getItem(JWT_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(JWT_KEY, token);
  } catch {
    /* storage blocked: stay signed in for this tab only via the store */
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(JWT_KEY);
  } catch {
    /* ignore */
  }
}

/** Bearer header when signed in, empty otherwise. */
export function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

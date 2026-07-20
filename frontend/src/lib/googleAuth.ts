/**
 * The browser half of the OAuth flow. The SPA sends the user to Google with a
 * one-time `state` it stashes locally; Google returns to the callback route
 * with a `code` and echoes the `state`. Comparing the echoed state to what we
 * stored is the CSRF check — a login response we didn't initiate won't match.
 */
const STATE_KEY = "lumina_oauth_state";
const AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth";

function randomState(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

/** Redirect the browser to Google's consent screen. */
export function startGoogleLogin(clientId: string, redirectUri: string): void {
  const state = randomState();
  try {
    sessionStorage.setItem(STATE_KEY, state);
  } catch {
    /* private mode: the callback will skip the state check and rely on the
       single-use code, which Google binds to our client secret */
  }
  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: redirectUri,
    response_type: "code",
    scope: "openid email profile",
    state,
    prompt: "select_account",
  });
  window.location.assign(`${AUTHORIZE_URL}?${params.toString()}`);
}

/** True if the state Google echoed matches the one we stored (or none was
 * stored, e.g. blocked sessionStorage). Consumes the stored value either way. */
export function consumeStateOk(returnedState: string | null): boolean {
  let stored: string | null;
  try {
    stored = sessionStorage.getItem(STATE_KEY);
    sessionStorage.removeItem(STATE_KEY);
  } catch {
    stored = null;
  }
  if (!stored) return true;
  return !!returnedState && returnedState === stored;
}

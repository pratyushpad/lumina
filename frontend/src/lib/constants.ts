/**
 * The seeded session every visitor shares. It is readable by anyone and
 * mutable by no one — the API enforces that; the UI just avoids offering
 * buttons that would come back 403.
 *
 * Chat still works on it: each visitor's turns are stored against their own
 * browser token, so the conversation is private even though the corpus is not.
 */
export const DEMO_SESSION_ID = "demo";

export function isDemoSession(sessionId: string): boolean {
  return sessionId === DEMO_SESSION_ID;
}

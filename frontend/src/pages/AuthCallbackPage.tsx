import { motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "@/lib/api";
import { consumeStateOk } from "@/lib/googleAuth";
import { useAuthStore } from "@/stores/authStore";

/**
 * Where Google returns after consent. Verifies the CSRF state, exchanges the
 * code for a session token, adopts this browser's anonymous sessions, then
 * hands off to the app. A failure here is not fatal — the user can keep using
 * Lumina signed out — so we explain and offer a way back.
 */
export default function AuthCallbackPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const setSession = useAuthStore((s) => s.setSession);
  const [error, setError] = useState<string | null>(null);
  // React 18 StrictMode double-invokes effects in dev; the code is single-use,
  // so guard against exchanging it twice.
  const ran = useRef(false);

  useEffect(() => {
    if (ran.current) return;
    ran.current = true;

    // All work runs after an await so state is never set synchronously during
    // the effect (and the auth code, which is single-use, is exchanged once).
    (async () => {
      await Promise.resolve();
      const code = params.get("code");
      const returnedState = params.get("state");
      const googleError = params.get("error");

      if (googleError) return setError("Sign-in was cancelled.");
      if (!code) return setError("That sign-in link was incomplete.");
      if (!consumeStateOk(returnedState))
        return setError("Sign-in could not be verified. Please try again.");

      try {
        const { token, user } = await api.exchangeCode(code);
        setSession(token, user);
        // Adopt anything created before signing in; non-fatal if it fails.
        await api.claim().catch(() => undefined);
        navigate("/app", { replace: true });
      } catch {
        setError("We couldn't complete sign-in with Google.");
      }
    })();
  }, [params, navigate, setSession]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6 text-textPrimary">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-sm text-center"
      >
        {error ? (
          <>
            <div className="text-[10px] uppercase tracking-tight2 text-textMuted font-mono">
              Sign-in
            </div>
            <h1 className="mt-3 font-display text-2xl font-bold tracking-tight2">
              Something went wrong
            </h1>
            <p className="mt-3 text-sm text-textSecondary">{error}</p>
            <button
              onClick={() => navigate("/app", { replace: true })}
              className="mt-6 hairline-strong bg-textPrimary px-4 py-2 text-sm font-medium text-background transition-colors hover:bg-textPrimary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
            >
              Continue to Lumina
            </button>
          </>
        ) : (
          <>
            <div className="mx-auto h-6 w-6 animate-spin rounded-full border-2 border-line border-t-accent" />
            <p className="mt-4 text-sm text-textSecondary">Finishing sign-in…</p>
          </>
        )}
      </motion.div>
    </div>
  );
}

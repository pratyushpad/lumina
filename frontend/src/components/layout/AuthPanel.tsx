import { LogOut } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { startGoogleLogin } from "@/lib/googleAuth";
import { useAuthStore } from "@/stores/authStore";

interface AuthConfig {
  enabled: boolean;
  clientId: string;
  redirectUri: string;
}

/**
 * Sidebar footer: sign in with Google, or the signed-in account with a way out.
 * Renders nothing at all when sign-in is not configured — the app is fully
 * usable anonymously, so there is no dead button to explain.
 */
export function AuthPanel() {
  const user = useAuthStore((s) => s.user);
  const signOut = useAuthStore((s) => s.signOut);
  const [cfg, setCfg] = useState<AuthConfig | null>(null);

  useEffect(() => {
    api
      .getConfig()
      .then((c) =>
        setCfg({
          enabled: c.auth_enabled,
          clientId: c.google_client_id,
          redirectUri: c.oauth_redirect_uri,
        }),
      )
      .catch(() => setCfg({ enabled: false, clientId: "", redirectUri: "" }));
  }, []);

  if (!cfg?.enabled) return null;

  const handleSignOut = () => {
    signOut();
    // The session/document/chat stores hold the previous identity's data;
    // a reload is the clean way to drop it and return to the anonymous view.
    window.location.assign("/app");
  };

  if (user) {
    const name = user.display_name || user.email || "Signed in";
    return (
      <div className="flex items-center gap-2.5 border-t border-line px-4 py-3">
        {user.avatar_url ? (
          <img
            src={user.avatar_url}
            alt=""
            referrerPolicy="no-referrer"
            className="h-7 w-7 shrink-0 rounded-full hairline"
          />
        ) : (
          <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-card text-xs font-semibold uppercase text-textSecondary">
            {name.charAt(0)}
          </span>
        )}
        <div className="min-w-0 flex-1">
          <div className="truncate text-xs font-medium text-textPrimary">{name}</div>
          <div className="text-[10px] uppercase tracking-tight2 text-textMuted font-mono">
            Saved to your account
          </div>
        </div>
        <button
          onClick={handleSignOut}
          aria-label="Sign out"
          className="shrink-0 text-textMuted transition-colors hover:text-textPrimary focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
        >
          <LogOut size={14} />
        </button>
      </div>
    );
  }

  return (
    <div className="border-t border-line px-3 py-3">
      <button
        onClick={() => startGoogleLogin(cfg.clientId, cfg.redirectUri)}
        className="flex w-full items-center justify-center gap-2 hairline bg-card px-3 py-2 text-xs font-medium text-textSecondary transition-colors hover:border-textPrimary/30 hover:text-textPrimary focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        <GoogleMark />
        Sign in to save your work
      </button>
    </div>
  );
}

function GoogleMark() {
  // Inline SVG (no external asset, CSP-safe). Google's four-colour "G".
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true" className="shrink-0">
      <path
        fill="#4285F4"
        d="M23.52 12.27c0-.82-.07-1.6-.2-2.36H12v4.47h6.46a5.52 5.52 0 0 1-2.4 3.62v3h3.87c2.26-2.09 3.59-5.17 3.59-8.73z"
      />
      <path
        fill="#34A853"
        d="M12 24c3.24 0 5.96-1.08 7.95-2.91l-3.88-3.01c-1.08.72-2.45 1.15-4.07 1.15-3.13 0-5.78-2.11-6.73-4.96H1.28v3.11A12 12 0 0 0 12 24z"
      />
      <path fill="#FBBC05" d="M5.27 14.27a7.2 7.2 0 0 1 0-4.54v-3.1H1.28a12 12 0 0 0 0 10.75z" />
      <path
        fill="#EA4335"
        d="M12 4.77c1.76 0 3.35.61 4.6 1.8l3.42-3.42A11.97 11.97 0 0 0 12 0 12 12 0 0 0 1.28 6.62l3.99 3.11C6.22 6.88 8.87 4.77 12 4.77z"
      />
    </svg>
  );
}

import { create } from "zustand";
import { api } from "@/lib/api";
import { clearToken, getToken, setToken } from "@/lib/auth";
import type { AuthUser } from "@/types";

interface AuthState {
  user: AuthUser | null;
  // undefined = not yet checked; keeps the UI from flashing "signed out" on load.
  ready: boolean;
  setSession: (token: string, user: AuthUser) => void;
  hydrate: () => Promise<void>;
  signOut: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  ready: false,

  setSession: (token, user) => {
    setToken(token);
    set({ user, ready: true });
  },

  /** On boot, turn a stored token into a user (or clear it if stale). */
  hydrate: async () => {
    if (!getToken()) {
      set({ user: null, ready: true });
      return;
    }
    try {
      const user = await api.me();
      set({ user, ready: true });
    } catch {
      // Token expired or revoked: drop it and continue as anonymous.
      clearToken();
      set({ user: null, ready: true });
    }
  },

  signOut: () => {
    clearToken();
    set({ user: null });
  },
}));

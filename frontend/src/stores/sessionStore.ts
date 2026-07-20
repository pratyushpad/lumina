import { create } from "zustand";
import type { Session } from "@/types";

interface SessionStore {
  sessions: Session[];
  activeSessionId: string | null;
  setSessions: (s: Session[]) => void;
  setActiveSession: (id: string | null) => void;
  addSession: (s: Session) => void;
  removeSession: (id: string) => void;
  updateSession: (id: string, patch: Partial<Session>) => void;
}

export const useSessionStore = create<SessionStore>((set) => ({
  sessions: [],
  activeSessionId: null,
  setSessions: (sessions) => set({ sessions }),
  setActiveSession: (id) => set({ activeSessionId: id }),
  addSession: (s) => set((st) => ({ sessions: [s, ...st.sessions] })),
  removeSession: (id) =>
    set((st) => ({
      sessions: st.sessions.filter((x) => x.id !== id),
      activeSessionId: st.activeSessionId === id ? null : st.activeSessionId,
    })),
  updateSession: (id, patch) =>
    set((st) => ({ sessions: st.sessions.map((x) => (x.id === id ? { ...x, ...patch } : x)) })),
}));

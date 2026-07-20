import { motion } from "framer-motion";
import { Check, Lock, Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
import { api } from "@/lib/api";
import { isDemoSession } from "@/lib/constants";
import { useSessionStore } from "@/stores/sessionStore";
import { toast } from "@/stores/toastStore";
import type { Session } from "@/types";

export function SessionList() {
  const sessions = useSessionStore((s) => s.sessions);
  const activeId = useSessionStore((s) => s.activeSessionId);
  const setActive = useSessionStore((s) => s.setActiveSession);
  const remove = useSessionStore((s) => s.removeSession);
  const update = useSessionStore((s) => s.updateSession);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");

  const handleDelete = async (e: React.MouseEvent, s: Session) => {
    e.stopPropagation();
    if (!confirm(`Delete session "${s.name}"?`)) return;
    try {
      await api.deleteSession(s.id);
      remove(s.id);
    } catch {
      toast.error("Could not delete session", "It may already be gone. Refresh and try again.");
    }
  };

  const startEditing = (e: React.MouseEvent, s: Session) => {
    e.stopPropagation();
    setEditingId(s.id);
    setDraft(s.name);
  };

  const commitRename = async (s: Session) => {
    const name = draft.trim();
    setEditingId(null);
    if (!name || name === s.name) return;
    // Optimistic: the sidebar updates immediately, and reverts if the API says no.
    update(s.id, { name });
    try {
      await api.renameSession(s.id, name);
    } catch {
      update(s.id, { name: s.name });
      toast.error("Could not rename session", "The change was not saved.");
    }
  };

  if (sessions.length === 0) {
    return (
      <div className="text-[11px] uppercase tracking-tight2 text-textMuted px-1 py-2">
        No sessions yet
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      {sessions.map((s) => {
        const active = s.id === activeId;
        const readOnly = isDemoSession(s.id);
        const editing = editingId === s.id && !readOnly;
        return (
          <motion.div
            key={s.id}
            whileHover={{ x: editing ? 0 : 1 }}
            onClick={() => !editing && setActive(s.id)}
            className={`group relative px-3 py-2.5 text-sm transition-colors ${
              editing ? "" : "cursor-pointer"
            } ${
              active
                ? "bg-card text-textPrimary accent-bar"
                : "text-textSecondary hover:bg-card/60 hover:text-textPrimary"
            }`}
          >
            <div className="flex items-center gap-2">
              <span className={`h-1.5 w-1.5 shrink-0 ${active ? "bg-accent" : "bg-textMuted"}`} />
              {editing ? (
                <input
                  autoFocus
                  value={draft}
                  aria-label="Session name"
                  onChange={(e) => setDraft(e.target.value)}
                  onClick={(e) => e.stopPropagation()}
                  onBlur={() => commitRename(s)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      commitRename(s);
                    } else if (e.key === "Escape") {
                      e.preventDefault();
                      setEditingId(null);
                    }
                  }}
                  className="min-w-0 flex-1 hairline bg-background px-1.5 py-0.5 text-sm font-medium tracking-tight2 outline-none focus:border-textPrimary/40"
                />
              ) : (
                <span className="truncate font-medium tracking-tight2">{s.name}</span>
              )}
              {editing ? (
                <button
                  onMouseDown={(e) => e.preventDefault()} // keep focus so blur does not double-commit
                  onClick={(e) => {
                    e.stopPropagation();
                    commitRename(s);
                  }}
                  aria-label="Save name"
                  className="ml-auto shrink-0 text-textMuted hover:text-textPrimary transition-colors"
                >
                  <Check size={13} />
                </button>
              ) : readOnly ? (
                // The demo is shared: renaming or deleting it would change what
                // every other visitor sees, so those affordances are not shown.
                <span
                  title="Shared demo — read-only"
                  className="ml-auto shrink-0 text-textMuted"
                  aria-hidden="true"
                >
                  <Lock size={11} />
                </span>
              ) : (
                <span className="ml-auto flex shrink-0 items-center gap-1.5 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
                  <button
                    onClick={(e) => startEditing(e, s)}
                    aria-label={`Rename ${s.name}`}
                    className="text-textMuted hover:text-textPrimary transition-colors"
                  >
                    <Pencil size={12} />
                  </button>
                  <button
                    onClick={(e) => handleDelete(e, s)}
                    aria-label={`Delete ${s.name}`}
                    className="text-textMuted hover:text-textPrimary transition-colors"
                  >
                    <Trash2 size={13} />
                  </button>
                </span>
              )}
            </div>
            <div className="mt-1 text-[10px] uppercase tracking-tight2 text-textMuted font-mono">
              {s.document_count} docs · {s.message_count} msgs
              {readOnly && " · shared"}
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}

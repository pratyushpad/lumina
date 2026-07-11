import { motion } from "framer-motion";
import { useEffect } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { ChatArea } from "@/components/chat/ChatArea";
import { DocumentPanel } from "@/components/chat/DocumentPanel";
import { useDocumentStatusPolling } from "@/hooks/useDocumentStatus";
import { api } from "@/lib/api";
import { useDocumentStore } from "@/stores/documentStore";
import { useSessionStore } from "@/stores/sessionStore";

export default function AppPage() {
  const sessions = useSessionStore((s) => s.sessions);
  const setSessions = useSessionStore((s) => s.setSessions);
  const activeSessionId = useSessionStore((s) => s.activeSessionId);
  const setDocuments = useDocumentStore((s) => s.setDocuments);

  useEffect(() => {
    api.listSessions().then((r) => setSessions(r.sessions));
  }, [setSessions]);

  useEffect(() => {
    if (activeSessionId) {
      api.listDocuments(activeSessionId).then((d) => setDocuments(activeSessionId, d));
    }
  }, [activeSessionId, setDocuments]);

  useDocumentStatusPolling(activeSessionId);

  return (
    <div className="flex h-screen bg-background text-white">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-hidden">
        {!activeSessionId ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-1 items-center justify-center px-6"
          >
            <div className="text-center max-w-md">
              <div className="text-[10px] uppercase tracking-tight2 text-textMuted font-mono">
                01 / Begin
              </div>
              <h2 className="mt-3 font-display text-4xl font-bold tracking-tight3">
                Select or create<br />a session.
              </h2>
              <p className="mt-4 text-sm text-textSecondary">
                {sessions.length === 0
                  ? "Hit New session in the sidebar to start."
                  : "Pick one from the sidebar, or create a new one."}
              </p>
              <div className="mt-8 inline-flex items-center gap-2 hairline bg-card px-3 py-1.5 text-[10px] uppercase tracking-tight2 text-textMuted font-mono">
                <span className="h-1.5 w-1.5 bg-accent" />
                Ready
              </div>
            </div>
          </motion.div>
        ) : (
          <>
            <DocumentPanel sessionId={activeSessionId} />
            <ChatArea sessionId={activeSessionId} />
          </>
        )}
      </main>
    </div>
  );
}

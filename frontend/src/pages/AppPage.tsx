import { motion, useReducedMotion } from "framer-motion";
import { MessagesSquare } from "lucide-react";
import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { Sidebar } from "@/components/layout/Sidebar";
import { ChatArea } from "@/components/chat/ChatArea";
import { DocumentPanel } from "@/components/chat/DocumentPanel";
import { useDocumentStatusPolling } from "@/hooks/useDocumentStatus";
import { api } from "@/lib/api";
import { DEMO_SESSION_ID } from "@/lib/constants";
import { duration, ease, fadeRise, staggerStep } from "@/lib/motion";
import { useAuthStore } from "@/stores/authStore";
import { useDocumentStore } from "@/stores/documentStore";
import { useSessionStore } from "@/stores/sessionStore";
import { toast } from "@/stores/toastStore";

const EMPTY_STATE_FEATURES = ["Hybrid retrieval", "Cited answers", "Query trace"];

const DEMO_SUGGESTIONS = [
  {
    label: "Why is dot-product attention scaled by 1/√dk?",
    query: "Why does the Transformer scale dot-product attention by 1 over the square root of d_k?",
  },
  {
    label: "How do residual connections help train very deep networks?",
    query:
      "According to the ResNet paper, how do residual connections help train very deep networks?",
  },
  {
    label: "What BLEU score did the Transformer get on WMT14 En→De?",
    query:
      "What BLEU score did the Transformer achieve on the WMT 2014 English-to-German translation task?",
  },
  {
    label: "What's the capital of France? (off-topic — watch it refuse)",
    query: "What is the capital of France?",
    guardrail: true,
  },
];

export default function AppPage() {
  const sessions = useSessionStore((s) => s.sessions);
  const setSessions = useSessionStore((s) => s.setSessions);
  const activeSessionId = useSessionStore((s) => s.activeSessionId);
  const setActiveSession = useSessionStore((s) => s.setActiveSession);
  const setDocuments = useDocumentStore((s) => s.setDocuments);
  const hydrateAuth = useAuthStore((s) => s.hydrate);
  const [searchParams, setSearchParams] = useSearchParams();
  const reduceMotion = useReducedMotion();

  // Turn a stored session token into a signed-in user (or drop it if stale).
  useEffect(() => {
    hydrateAuth();
  }, [hydrateAuth]);

  useEffect(() => {
    api
      .listSessions()
      .then((r) => {
        setSessions(r.sessions);
        const requested = searchParams.get("session");
        if (!requested) return;
        if (r.sessions.some((s) => s.id === requested)) {
          setActiveSession(requested);
        } else {
          // Landing links straight to ?session=demo; if seeding has not run the
          // user would otherwise get a blank pane with no explanation.
          toast.error(
            "That session isn't available",
            requested === "demo"
              ? "The demo is still being prepared on the server. Try again shortly, or upload your own document."
              : "It may have been deleted.",
          );
        }
        setSearchParams({}, { replace: true });
      })
      .catch(() =>
        toast.error(
          "Could not reach the server",
          "The free-tier API may be waking up. Give it up to a minute and refresh.",
        ),
      );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [setSessions]);

  useEffect(() => {
    if (activeSessionId) {
      api.listDocuments(activeSessionId).then((d) => setDocuments(activeSessionId, d));
    }
  }, [activeSessionId, setDocuments]);

  useDocumentStatusPolling(activeSessionId);

  return (
    <div className="flex h-screen bg-background text-textPrimary">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-hidden">
        {!activeSessionId ? (
          <motion.div
            initial={reduceMotion ? "visible" : "hidden"}
            animate="visible"
            variants={{
              hidden: {},
              visible: { transition: { staggerChildren: staggerStep, delayChildren: 0.05 } },
            }}
            className="flex flex-1 items-center justify-center px-6"
          >
            <div className="max-w-md hairline-strong bg-surface px-8 py-10 text-center">
              <motion.div
                variants={fadeRise}
                transition={{ duration: duration.base, ease }}
                className="mx-auto mb-6 flex h-12 w-12 items-center justify-center hairline bg-card"
              >
                <MessagesSquare size={20} className="text-accent" strokeWidth={1.75} />
              </motion.div>
              <motion.div
                variants={fadeRise}
                transition={{ duration: duration.base, ease }}
                className="font-mono text-[10px] uppercase tracking-tight2 text-textMuted"
              >
                Workbench idle
              </motion.div>
              <motion.h2
                variants={fadeRise}
                transition={{ duration: duration.base, ease }}
                className="mt-3 font-display text-4xl font-bold tracking-tight3"
              >
                Select or create
                <br />a session.
              </motion.h2>
              <motion.p
                variants={fadeRise}
                transition={{ duration: duration.base, ease }}
                className="mt-4 text-sm text-textSecondary"
              >
                {sessions.length === 0
                  ? "Hit New session in the sidebar to start."
                  : "Pick one from the sidebar, or create a new one."}
              </motion.p>
              <motion.div
                variants={fadeRise}
                transition={{ duration: duration.base, ease }}
                className="mt-8 flex flex-wrap items-center justify-center gap-2 border-t border-line pt-6"
              >
                {EMPTY_STATE_FEATURES.map((f) => (
                  <span
                    key={f}
                    className="hairline bg-card px-2.5 py-1 text-[10px] font-mono uppercase tracking-tight2 text-textMuted"
                  >
                    {f}
                  </span>
                ))}
              </motion.div>
              <motion.div
                variants={fadeRise}
                transition={{ duration: duration.base, ease }}
                className="mt-6 inline-flex items-center gap-2 hairline bg-card px-3 py-1.5 text-[10px] uppercase tracking-tight2 text-textMuted font-mono"
              >
                <span className="h-1.5 w-1.5 bg-accent" />
                Ready
              </motion.div>
            </div>
          </motion.div>
        ) : (
          <>
            <DocumentPanel sessionId={activeSessionId} />
            <ChatArea
              sessionId={activeSessionId}
              suggestions={activeSessionId === DEMO_SESSION_ID ? DEMO_SUGGESTIONS : undefined}
            />
          </>
        )}
      </main>
    </div>
  );
}

import { useEffect, useRef } from "react";
import { api } from "@/lib/api";
import { useDocumentStore } from "@/stores/documentStore";
import { toast } from "@/stores/toastStore";

export function useDocumentStatusPolling(sessionId: string | null) {
  const documents = useDocumentStore((s) => (sessionId ? s.documents[sessionId] || [] : []));
  const updateDocument = useDocumentStore((s) => s.updateDocument);
  const notifiedRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!sessionId) return;
    const processing = documents.filter((d) => d.status === "processing");
    if (processing.length === 0) return;
    const interval = setInterval(async () => {
      for (const d of processing) {
        if (notifiedRef.current.has(d.id)) continue;
        try {
          const status = await api.getDocumentStatus(d.id);
          if (status.status === "ready") {
            notifiedRef.current.add(d.id);
            updateDocument(sessionId, d.id, {
              status: "ready",
              num_chunks: status.num_chunks,
            });
            toast.success(`${d.filename} ready`, `${status.num_chunks} chunks indexed`);
          } else if (status.status === "error") {
            notifiedRef.current.add(d.id);
            updateDocument(sessionId, d.id, {
              status: "error",
              error_message: status.error_message,
            });
            toast.error(`Failed to process ${d.filename}`, status.error_message ?? undefined);
          }
        } catch {
          /* ignore — next tick retries */
        }
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [sessionId, documents, updateDocument]);
}

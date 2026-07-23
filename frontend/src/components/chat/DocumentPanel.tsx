import { motion, useReducedMotion } from "framer-motion";
import { FileText, Image as ImageIcon, Lock, X } from "lucide-react";
import { useState } from "react";
import { DocumentDropzone } from "@/components/upload/DocumentDropzone";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { api } from "@/lib/api";
import { isDemoSession } from "@/lib/constants";
import { useDocumentStore } from "@/stores/documentStore";
import { toast } from "@/stores/toastStore";
import type { Document } from "@/types";

function StatusBadge({ status }: { status: Document["status"] }) {
  const map = {
    processing: {
      cls: "text-warn border-warn/40",
      label: "PROCESSING",
      dot: "bg-warn animate-pulse",
    },
    ready: { cls: "text-ok border-ok/40", label: "READY", dot: "bg-ok" },
    error: { cls: "text-error border-error/40", label: "ERROR", dot: "bg-error" },
  } as const;
  const v = map[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 border px-2 py-0.5 text-[9px] font-mono uppercase tracking-tight2 ${v.cls}`}
    >
      <span className={`h-1.5 w-1.5 ${v.dot}`} />
      {v.label}
    </span>
  );
}

export function DocumentPanel({ sessionId }: { sessionId: string }) {
  const docs = useDocumentStore((s) => s.documents[sessionId] || []);
  const removeDocument = useDocumentStore((s) => s.removeDocument);
  const readOnly = isDemoSession(sessionId);
  const reduceMotion = useReducedMotion();
  const [pendingDelete, setPendingDelete] = useState<{ id: string; filename: string } | null>(null);

  const confirmDelete = async () => {
    if (!pendingDelete) return;
    const { id } = pendingDelete;
    setPendingDelete(null);
    try {
      await api.deleteDocument(id);
      removeDocument(sessionId, id);
    } catch {
      toast.error("Could not remove document", "It may already be gone. Refresh and try again.");
    }
  };

  return (
    <div className="border-b border-line bg-background px-6 py-4">
      <div className="flex flex-wrap items-center gap-2">
        {readOnly ? (
          <span className="inline-flex items-center gap-1.5 hairline bg-card px-3 py-2 text-[10px] font-mono uppercase tracking-tight2 text-textMuted">
            <Lock size={11} />
            Shared library — ask anything, uploads go in your own session
          </span>
        ) : (
          <DocumentDropzone sessionId={sessionId} />
        )}
        {docs.map((d) => (
          <motion.div
            key={d.id}
            initial={reduceMotion ? false : { opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="group flex items-center gap-2.5 hairline bg-card px-3 py-2 text-sm"
          >
            {d.file_type === "image" ? (
              <ImageIcon size={14} className="text-textSecondary" />
            ) : (
              <FileText size={14} className="text-textSecondary" />
            )}
            <span className="max-w-[180px] truncate font-medium">{d.filename}</span>
            <span className="text-[10px] font-mono uppercase tracking-tight2 text-textMuted">
              {d.num_chunks} chunks
            </span>
            <StatusBadge status={d.status} />
            {!readOnly && (
              <button
                onClick={() => setPendingDelete({ id: d.id, filename: d.filename })}
                aria-label={`Remove ${d.filename}`}
                className="ml-1 opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100 text-textMuted hover:text-textPrimary"
              >
                <X size={13} />
              </button>
            )}
          </motion.div>
        ))}
      </div>
      <ConfirmDialog
        open={!!pendingDelete}
        title="Remove document"
        description={
          pendingDelete
            ? `Remove "${pendingDelete.filename}" from this session? This can't be undone.`
            : undefined
        }
        confirmLabel="Remove"
        destructive
        onConfirm={confirmDelete}
        onCancel={() => setPendingDelete(null)}
      />
    </div>
  );
}

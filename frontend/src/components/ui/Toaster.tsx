import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";
import { useToastStore, type Toast } from "@/stores/toastStore";

const ICONS = { success: CheckCircle2, error: AlertCircle, info: Info } as const;
const ACCENT = {
  success: "border-l-2 border-white",
  error: "border-l-2 border-rose-400",
  info: "border-l-2 border-accent",
} as const;
const ICON_COLOR = {
  success: "text-white",
  error: "text-rose-400",
  info: "text-accent",
} as const;

function ToastCard({ t }: { t: Toast }) {
  const dismiss = useToastStore((s) => s.dismiss);
  const Icon = ICONS[t.kind];
  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 30 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 40, transition: { duration: 0.18 } }}
      className={`pointer-events-auto flex w-[340px] items-start gap-3 hairline bg-surface ${ACCENT[t.kind]} p-3.5`}
    >
      <Icon size={16} className={`mt-0.5 shrink-0 ${ICON_COLOR[t.kind]}`} />
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-white tracking-tight2">{t.title}</div>
        {t.message && (
          <div className="mt-1 text-[11px] text-textSecondary line-clamp-3 font-mono">
            {t.message}
          </div>
        )}
      </div>
      <button
        onClick={() => dismiss(t.id)}
        className="text-textMuted hover:text-white transition-colors"
      >
        <X size={13} />
      </button>
    </motion.div>
  );
}

export function Toaster() {
  const toasts = useToastStore((s) => s.toasts);
  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      <AnimatePresence mode="popLayout">
        {toasts.map((t) => (
          <ToastCard key={t.id} t={t} />
        ))}
      </AnimatePresence>
    </div>
  );
}

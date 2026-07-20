import { motion, useReducedMotion } from "framer-motion";
import { ArrowLeft } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { GradientButton } from "@/components/ui/GradientButton";
import { duration, ease } from "@/lib/motion";

export default function NotFoundPage() {
  const { pathname } = useLocation();
  const reduce = useReducedMotion();

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6 noise">
      <motion.div
        initial={{ opacity: 0, y: reduce ? 0 : 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: duration.slow, ease }}
        className="w-full max-w-lg"
      >
        <div className="font-mono text-[10px] uppercase tracking-tight2 text-textMuted">
          Error 404
        </div>
        <h1 className="mt-3 font-display text-6xl font-bold leading-[0.95] tracking-tight3 text-balance">
          Nothing here<span className="text-accent">.</span>
        </h1>
        <p className="mt-5 text-sm leading-relaxed text-textSecondary">
          No page matches <span className="font-mono text-textPrimary break-all">{pathname}</span>.
          It may have moved, or the link may be wrong.
        </p>
        <div className="mt-9 flex flex-wrap items-center gap-3">
          <Link to="/">
            <GradientButton variant="primary">
              <ArrowLeft size={14} /> Back home
            </GradientButton>
          </Link>
          <Link to="/app">
            <GradientButton variant="outline">Open Lumina</GradientButton>
          </Link>
        </div>
      </motion.div>
    </div>
  );
}

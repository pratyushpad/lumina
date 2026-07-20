import { AnimatePresence, motion } from "framer-motion";
import { FileText, Image as ImageIcon } from "lucide-react";
import { useState } from "react";
import { imageUrl } from "@/lib/api";
import { duration, ease, springPress } from "@/lib/motion";
import type { Citation } from "@/types";

function scoreColor(score: number) {
  if (score >= 0.8) return "bg-accent";
  if (score >= 0.5) return "bg-textSecondary";
  return "bg-textMuted";
}

export function CitationChip({ citation }: { citation: Citation }) {
  const [open, setOpen] = useState(false);
  const [imageFailed, setImageFailed] = useState(false);
  const Icon = citation.has_image ? ImageIcon : FileText;
  const src = citation.image_path ? imageUrl(citation.image_path) : null;

  return (
    <div className="inline-block">
      <motion.button
        whileHover={{ y: -1 }}
        whileTap={{ scale: 0.97 }}
        transition={springPress}
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="inline-flex items-center gap-2 hairline bg-card px-3 py-1.5 text-[11px] uppercase tracking-tight2 text-textSecondary hover:text-textPrimary hover:border-textPrimary/40 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        <Icon size={11} />
        <span className="font-mono normal-case text-textPrimary truncate max-w-[180px]">
          {citation.filename}
        </span>
        {citation.page_num != null && <span className="font-mono">p.{citation.page_num}</span>}
        <span className={`h-1.5 w-1.5 ${scoreColor(citation.relevance_score)}`} />
      </motion.button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: duration.base, ease }}
            className="mt-2 overflow-hidden hairline bg-background p-3 text-xs text-textSecondary font-mono leading-relaxed"
          >
            {/* The cited region of the page, when this chunk came from an image
                or a figure the vision model described. */}
            {src && !imageFailed && (
              <img
                src={src}
                alt={`Cited figure from ${citation.filename}${
                  citation.page_num != null ? `, page ${citation.page_num}` : ""
                }`}
                loading="lazy"
                onError={() => setImageFailed(true)}
                className="mb-3 max-h-64 w-auto max-w-full hairline bg-card object-contain"
              />
            )}
            {citation.chunk_text}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { CitationChip } from "./CitationChip";
import type { Citation } from "@/types";

interface Props {
  content: string;
  citations?: Citation[];
  streaming?: boolean;
}

export function StreamingMessage({ content, citations, streaming }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="hairline bg-surface p-5 max-w-[85%]"
    >
      <div className="prose prose-invert prose-sm max-w-none prose-headings:font-display prose-headings:tracking-tight2 prose-p:my-2 prose-code:bg-card prose-code:px-1 prose-code:py-0.5 prose-code:before:content-[''] prose-code:after:content-['']">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        {streaming && (
          <span className="ml-0.5 inline-block h-3.5 w-2 bg-accent align-middle animate-pulse" />
        )}
      </div>
      {citations && citations.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2 border-t border-line pt-4">
          {citations.map((c) => (
            <CitationChip key={c.chunk_id} citation={c} />
          ))}
        </div>
      )}
    </motion.div>
  );
}

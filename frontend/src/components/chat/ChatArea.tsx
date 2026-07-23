import { motion, useReducedMotion } from "framer-motion";
import { ArrowUp, Square } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { StreamingMessage } from "./StreamingMessage";
import { api, streamChat } from "@/lib/api";
import { springPress } from "@/lib/motion";
import { useChatStore } from "@/stores/chatStore";
import { toast } from "@/stores/toastStore";
import type { Message } from "@/types";

const MAX_TEXTAREA_PX = 200;

export function ChatArea({
  sessionId,
  suggestions,
}: {
  sessionId: string;
  suggestions?: { label: string; query: string; guardrail?: boolean }[];
}) {
  const messages = useChatStore((s) => s.messages[sessionId] || []);
  const setMessages = useChatStore((s) => s.setMessages);
  const addMessage = useChatStore((s) => s.addMessage);
  const streamingContent = useChatStore((s) => s.streamingContent);
  const streamingCitations = useChatStore((s) => s.streamingCitations);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const setStreaming = useChatStore((s) => s.setStreaming);
  const appendToken = useChatStore((s) => s.appendToken);
  const setStreamingCitations = useChatStore((s) => s.setStreamingCitations);
  const setStreamingMeta = useChatStore((s) => s.setStreamingMeta);
  const clearStream = useChatStore((s) => s.clearStream);

  const reduceMotion = useReducedMotion();
  const [input, setInput] = useState("");
  const [model, setModel] = useState<string | null>(null);
  const [capacityNotice, setCapacityNotice] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const cleanupRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    api
      .getConfig()
      .then((c) => setModel(c.model))
      .catch(() => setModel(null));
  }, []);

  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, MAX_TEXTAREA_PX)}px`;
  }, [input]);

  useEffect(() => {
    api.getHistory(sessionId).then((m) => setMessages(sessionId, m as Message[]));
    return () => {
      cleanupRef.current?.();
      cleanupRef.current = null;
      clearStream();
    };
  }, [sessionId, setMessages, clearStream]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, streamingContent]);

  const send = (queryOverride?: string) => {
    const query = (queryOverride ?? input).trim();
    if (!query || isStreaming) return;
    setInput("");
    setCapacityNotice(null);
    addMessage(sessionId, {
      id: `tmp-${Date.now()}`,
      role: "user",
      content: query,
      created_at: new Date().toISOString(),
    });
    clearStream();
    setStreaming(true);
    cleanupRef.current = streamChat(sessionId, query, {
      onCitations: (c) => setStreamingCitations(c),
      onToken: (t) => appendToken(t),
      onMeta: (m) => setStreamingMeta(m),
      onCapacity: (message) => {
        // Not an error: the day's free-tier quota is spent. Keep the question in
        // place, surface a calm banner, and drop the empty assistant turn.
        setCapacityNotice(message);
        clearStream();
      },
      onDone: (messageId) => {
        const finalContent = useChatStore.getState().streamingContent;
        const finalCitations = useChatStore.getState().streamingCitations;
        const finalMeta = useChatStore.getState().streamingMeta;
        addMessage(sessionId, {
          id: messageId || `err-${Date.now()}`,
          role: "assistant",
          content: finalContent,
          citations: finalCitations,
          meta: finalMeta,
          model_used: finalMeta ? `${finalMeta.provider}:${finalMeta.model}` : null,
          created_at: new Date().toISOString(),
        });
        clearStream();
      },
      onError: (e) => {
        toast.error("Chat failed", e);
        addMessage(sessionId, {
          id: `err-${Date.now()}`,
          role: "assistant",
          content: `Error: ${e}`,
          created_at: new Date().toISOString(),
        });
        clearStream();
      },
    });
  };

  /**
   * Abort an in-flight generation. The partial answer is kept so the user can
   * read what arrived, but the server cancels its generator on disconnect and
   * never persists a stopped turn — so it is marked, and will not reappear on
   * reload.
   */
  const stop = () => {
    if (!isStreaming) return;
    const partial = useChatStore.getState().streamingContent;
    const citations = useChatStore.getState().streamingCitations;
    cleanupRef.current?.();
    cleanupRef.current = null;
    if (partial.trim()) {
      addMessage(sessionId, {
        id: `stopped-${Date.now()}`,
        role: "assistant",
        content: partial,
        citations,
        stopped: true,
        created_at: new Date().toISOString(),
      });
    }
    clearStream();
  };

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto px-6 py-10">
        <div className="mx-auto flex max-w-3xl flex-col gap-5">
          {messages.length === 0 && !isStreaming && suggestions && suggestions.length > 0 && (
            <motion.div
              initial={reduceMotion ? false : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center gap-6 pt-16 text-center"
            >
              <div>
                <div className="text-[10px] uppercase tracking-tight2 text-textMuted font-mono">
                  Demo session · two papers loaded
                </div>
                <h3 className="mt-2 font-display text-2xl font-bold tracking-tight2">
                  Ask these papers anything.
                </h3>
              </div>
              <div className="flex max-w-2xl flex-wrap justify-center gap-2">
                {suggestions.map((s) => (
                  <button
                    key={s.query}
                    onClick={() => send(s.query)}
                    className={`hairline px-3 py-2 text-left text-xs transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent ${
                      s.guardrail
                        ? "text-textMuted hover:text-textSecondary hover:border-textPrimary/20"
                        : "bg-card text-textSecondary hover:text-textPrimary hover:border-textPrimary/30"
                    }`}
                  >
                    {s.guardrail && (
                      <span className="mr-1.5 font-mono text-[9px] uppercase tracking-tight2 text-accent">
                        guardrail
                      </span>
                    )}
                    {s.label}
                  </button>
                ))}
              </div>
            </motion.div>
          )}
          {messages.map((m) =>
            m.role === "user" ? (
              <motion.div
                key={m.id}
                initial={reduceMotion ? false : { opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="self-end max-w-[85%] hairline-strong bg-textPrimary text-background px-4 py-2.5 text-sm font-medium tracking-tight2"
              >
                {m.content}
              </motion.div>
            ) : (
              <StreamingMessage
                key={m.id}
                content={m.content}
                citations={m.citations || []}
                meta={m.meta}
                modelUsed={m.model_used}
                messageId={m.id}
                stopped={m.stopped}
              />
            ),
          )}
          {isStreaming && (
            <StreamingMessage content={streamingContent} citations={streamingCitations} streaming />
          )}
          <div ref={bottomRef} />
        </div>
      </div>
      <div className="sticky bottom-0 border-t border-line bg-background p-4">
        <div className="mx-auto flex max-w-3xl flex-col gap-2">
          {capacityNotice && (
            <motion.div
              initial={reduceMotion ? false : { opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              role="status"
              className="flex items-start justify-between gap-3 hairline bg-card px-3 py-2 text-xs text-textSecondary"
            >
              <span>{capacityNotice}</span>
              <button
                onClick={() => setCapacityNotice(null)}
                aria-label="Dismiss"
                className="shrink-0 font-mono text-[10px] uppercase tracking-tight2 text-textMuted hover:text-textPrimary transition-colors"
              >
                Dismiss
              </button>
            </motion.div>
          )}
          <div className="flex items-end gap-2">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                } else if (e.key === "Escape" && isStreaming) {
                  e.preventDefault();
                  stop();
                }
              }}
              placeholder="Ask your documents…"
              rows={1}
              style={{ maxHeight: `${MAX_TEXTAREA_PX}px` }}
              className="flex-1 resize-none overflow-y-auto hairline bg-card px-4 py-3 text-sm outline-none focus:border-textPrimary/30 transition-colors placeholder:text-textMuted"
            />
            {isStreaming ? (
              <motion.button
                whileTap={{ scale: 0.97 }}
                transition={springPress}
                onClick={stop}
                aria-label="Stop generating"
                className="hairline-strong bg-card text-textPrimary p-3 hover:border-textPrimary/40 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
              >
                <Square size={16} strokeWidth={2.5} fill="currentColor" />
              </motion.button>
            ) : (
              <motion.button
                whileTap={{ scale: 0.97 }}
                transition={springPress}
                onClick={() => send()}
                disabled={!input.trim()}
                aria-label="Send message"
                className="hairline-strong bg-textPrimary text-background p-3 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-textPrimary/90 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
              >
                <ArrowUp size={16} strokeWidth={2.5} />
              </motion.button>
            )}
          </div>
          <div className="flex items-center justify-between text-[10px] uppercase tracking-tight2 text-textMuted font-mono">
            <span>{isStreaming ? "esc stop" : "↵ send · ⇧↵ newline"}</span>
            {model && (
              <span className="inline-flex items-center gap-1.5 hairline bg-card px-2 py-1">
                <span className="h-1.5 w-1.5 bg-accent animate-pulse" />
                <span>{model}</span>
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

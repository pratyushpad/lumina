import type {
  Citation,
  Document,
  DocumentStatusResponse,
  DocumentUploadResponse,
  Message,
  Session,
  SessionListResponse,
  StreamMeta,
  Trace,
} from "@/types";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  // sessions
  createSession: (name?: string) =>
    http<Session>("/api/sessions/", { method: "POST", body: JSON.stringify({ name }) }),
  listSessions: () => http<SessionListResponse>("/api/sessions/"),
  getSession: (id: string) => http<Session>(`/api/sessions/${id}`),
  renameSession: (id: string, name: string) =>
    http<Session>(`/api/sessions/${id}`, { method: "PATCH", body: JSON.stringify({ name }) }),
  deleteSession: (id: string) =>
    http<{ message: string }>(`/api/sessions/${id}`, { method: "DELETE" }),

  // documents
  uploadDocument: async (sessionId: string, file: File): Promise<DocumentUploadResponse> => {
    const fd = new FormData();
    fd.append("session_id", sessionId);
    fd.append("file", file);
    const res = await fetch(`${BASE_URL}/api/documents/upload`, { method: "POST", body: fd });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  listDocuments: (sessionId: string) => http<Document[]>(`/api/documents/session/${sessionId}`),
  getDocumentStatus: (documentId: string) =>
    http<DocumentStatusResponse>(`/api/documents/${documentId}/status`),
  deleteDocument: (documentId: string) =>
    http<{ chunks_deleted: number }>(`/api/documents/${documentId}`, { method: "DELETE" }),

  // chat history
  getHistory: (sessionId: string) => http<Message[]>(`/api/chat/${sessionId}/history`),

  // traces
  getTrace: (messageId: string) => http<Trace>(`/api/traces/${messageId}`),

  // config (model name, limits)
  getConfig: () =>
    http<{
      model: string;
      max_file_size_mb: number;
      allowed_extensions: string[];
      top_k_reranked: number;
    }>("/api/config"),
};

/**
 * Absolute URL for a cited image. Accepts the `/static/images/<name>` path the
 * API returns, and tolerates the absolute server paths stored in citations from
 * before that changed, by falling back to the basename.
 */
export function imageUrl(imagePath: string): string {
  const name = imagePath.split(/[\\/]/).pop();
  return `${BASE_URL}/static/images/${name}`;
}

export interface StreamHandlers {
  onCitations: (c: Citation[]) => void;
  onToken: (t: string) => void;
  onMeta?: (m: StreamMeta) => void;
  onDone: (messageId?: string) => void;
  onError: (e: string) => void;
}

/**
 * Consume the SSE chat stream.
 *
 * Uses fetch + ReadableStream rather than EventSource for two reasons:
 * EventSource cannot send request headers (needed to identify the caller), and
 * it offers no way to abort a response mid-flight — so there was no way to stop
 * a running generation. Returns a cancel function.
 */
export function streamChat(sessionId: string, query: string, h: StreamHandlers): () => void {
  const url = `${BASE_URL}/api/chat/${sessionId}/stream?query=${encodeURIComponent(query)}`;
  const controller = new AbortController();
  let finished = false;

  const finish = () => {
    if (finished) return;
    finished = true;
    controller.abort();
  };

  const dispatch = (raw: string) => {
    const payload = JSON.parse(raw);
    if (payload.type === "citations") h.onCitations(payload.data || []);
    else if (payload.type === "token") h.onToken(payload.data || "");
    else if (payload.type === "meta") h.onMeta?.(payload.data);
    else if (payload.type === "refusal") h.onToken(payload.data || "");
    else if (payload.type === "done") {
      h.onDone(payload.data?.message_id);
      finish();
    } else if (payload.type === "error") {
      h.onError(payload.data || "stream error");
      finish();
    }
  };

  (async () => {
    try {
      const res = await fetch(url, {
        headers: { Accept: "text/event-stream" },
        signal: controller.signal,
      });
      if (!res.ok || !res.body) {
        // Error responses are JSON ({"error": "..."}), not a stream.
        let detail = `HTTP ${res.status}`;
        try {
          detail = (await res.json())?.error || detail;
        } catch {
          /* non-JSON body: keep the status line */
        }
        if (!finished) h.onError(detail);
        finish();
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // SSE frames are separated by a blank line. The separator may be
        // \r\n\r\n (what sse-starlette actually sends), \n\n, or \r\r, and a
        // frame can arrive split across chunks — so only complete frames are
        // consumed here.
        for (;;) {
          const m = /\r\n\r\n|\n\n|\r\r/.exec(buffer);
          if (!m) break;
          const frame = buffer.slice(0, m.index);
          buffer = buffer.slice(m.index + m[0].length);
          const data = frame
            .split(/\r\n|\n|\r/)
            .filter((l) => l.startsWith("data:"))
            .map((l) => l.slice(5).trim())
            .join("\n");
          if (data) dispatch(data);
        }
        if (finished) break;
      }
      // The server closed without a terminal event (deploy restart, timeout).
      if (!finished) {
        h.onError("The connection closed before the answer finished.");
        finish();
      }
    } catch (err) {
      // An abort is the user pressing Stop, not a failure.
      if (controller.signal.aborted) return;
      if (!finished) h.onError(err instanceof Error ? err.message : String(err));
      finish();
    }
  })();

  return finish;
}

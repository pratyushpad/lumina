// src/lib/api.ts
var BASE_URL = "http://test.local";
async function http(path, init) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers || {} },
    ...init
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}
var api = {
  // sessions
  createSession: (name) => http("/api/sessions/", { method: "POST", body: JSON.stringify({ name }) }),
  listSessions: () => http("/api/sessions/"),
  getSession: (id) => http(`/api/sessions/${id}`),
  renameSession: (id, name) => http(`/api/sessions/${id}`, { method: "PATCH", body: JSON.stringify({ name }) }),
  deleteSession: (id) => http(`/api/sessions/${id}`, { method: "DELETE" }),
  // documents
  uploadDocument: async (sessionId, file) => {
    const fd = new FormData();
    fd.append("session_id", sessionId);
    fd.append("file", file);
    const res = await fetch(`${BASE_URL}/api/documents/upload`, { method: "POST", body: fd });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  listDocuments: (sessionId) => http(`/api/documents/session/${sessionId}`),
  getDocumentStatus: (documentId) => http(`/api/documents/${documentId}/status`),
  deleteDocument: (documentId) => http(`/api/documents/${documentId}`, { method: "DELETE" }),
  // chat history
  getHistory: (sessionId) => http(`/api/chat/${sessionId}/history`),
  // traces
  getTrace: (messageId) => http(`/api/traces/${messageId}`),
  // config (model name, limits)
  getConfig: () => http("/api/config")
};
function imageUrl(imagePath) {
  const name = imagePath.split(/[\\/]/).pop();
  return `${BASE_URL}/static/images/${name}`;
}
function streamChat(sessionId, query, h) {
  const url = `${BASE_URL}/api/chat/${sessionId}/stream?query=${encodeURIComponent(query)}`;
  const controller = new AbortController();
  let finished = false;
  const finish = () => {
    if (finished) return;
    finished = true;
    controller.abort();
  };
  const dispatch = (raw) => {
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
        signal: controller.signal
      });
      if (!res.ok || !res.body) {
        let detail = `HTTP ${res.status}`;
        try {
          detail = (await res.json())?.error || detail;
        } catch {
        }
        if (!finished) h.onError(detail);
        finish();
        return;
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      for (; ; ) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let sep;
        while ((sep = buffer.indexOf("\n\n")) !== -1) {
          const frame = buffer.slice(0, sep);
          buffer = buffer.slice(sep + 2);
          const data = frame.split("\n").filter((l) => l.startsWith("data:")).map((l) => l.slice(5).trim()).join("\n");
          if (data) dispatch(data);
        }
        if (finished) break;
      }
      if (!finished) {
        h.onError("The connection closed before the answer finished.");
        finish();
      }
    } catch (err) {
      if (controller.signal.aborted) return;
      if (!finished) h.onError(err instanceof Error ? err.message : String(err));
      finish();
    }
  })();
  return finish;
}
export {
  api,
  imageUrl,
  streamChat
};

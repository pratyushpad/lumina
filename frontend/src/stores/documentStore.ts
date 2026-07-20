import { create } from "zustand";
import type { Document } from "@/types";

interface DocumentStore {
  documents: Record<string, Document[]>;
  setDocuments: (sessionId: string, docs: Document[]) => void;
  addDocument: (sessionId: string, doc: Document) => void;
  updateDocument: (sessionId: string, docId: string, patch: Partial<Document>) => void;
  removeDocument: (sessionId: string, docId: string) => void;
}

export const useDocumentStore = create<DocumentStore>((set) => ({
  documents: {},
  setDocuments: (sessionId, docs) =>
    set((s) => ({ documents: { ...s.documents, [sessionId]: docs } })),
  addDocument: (sessionId, doc) =>
    set((s) => ({
      documents: {
        ...s.documents,
        [sessionId]: [doc, ...(s.documents[sessionId] || [])],
      },
    })),
  updateDocument: (sessionId, docId, patch) =>
    set((s) => ({
      documents: {
        ...s.documents,
        [sessionId]: (s.documents[sessionId] || []).map((d) =>
          d.id === docId ? { ...d, ...patch } : d,
        ),
      },
    })),
  removeDocument: (sessionId, docId) =>
    set((s) => ({
      documents: {
        ...s.documents,
        [sessionId]: (s.documents[sessionId] || []).filter((d) => d.id !== docId),
      },
    })),
}));

"""ChromaDB persistent vector store singleton."""
import logging
from dataclasses import dataclass
from typing import Optional

import chromadb

from app.config import settings
from app.services.ingestion.chunker import ChunkData

logger = logging.getLogger("lumina.vectorstore")

COLLECTION_NAME = "lumina_chunks"


@dataclass
class RetrievalResult:
    chunk_id: str
    document_id: str
    text: str
    page_num: int
    filename: str
    distance: float
    has_associated_image: bool = False
    image_path: Optional[str] = None
    relevance_score: float = 0.0
    block_type: str = "text"


class VectorStore:
    _instance: Optional["VectorStore"] = None

    def __init__(self):
        logger.info("Connecting to ChromaDB at %s", settings.CHROMA_PERSIST_DIR)
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self.collection = self.client.get_or_create_collection(
            COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )
        logger.info("Vector store ready (count=%d)", self.collection.count())

    @classmethod
    def get(cls) -> "VectorStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_chunks(self, chunks: list[ChunkData], embeddings: list[list[float]]) -> int:
        if not chunks:
            return 0
        assert len(chunks) == len(embeddings), "chunks/embeddings length mismatch"
        total = 0
        batch = 100
        for i in range(0, len(chunks), batch):
            sub_chunks = chunks[i : i + batch]
            sub_embeds = embeddings[i : i + batch]
            ids = [c.chunk_id for c in sub_chunks]
            docs = [c.text for c in sub_chunks]
            metas = [
                {
                    "document_id": c.document_id,
                    "page_num": c.page_num,
                    "chunk_index": c.chunk_index,
                    "block_type": c.block_type,
                    "filename": c.filename,
                    "has_associated_image": bool(c.has_associated_image),
                    "image_path": c.image_path or "",
                }
                for c in sub_chunks
            ]
            self.collection.upsert(
                ids=ids, embeddings=sub_embeds, documents=docs, metadatas=metas
            )
            total += len(sub_chunks)
        return total

    def query(
        self, query_embedding: list[float], document_ids: list[str], top_k: int
    ) -> list[RetrievalResult]:
        if not document_ids:
            return []
        where = (
            {"document_id": document_ids[0]}
            if len(document_ids) == 1
            else {"document_id": {"$in": document_ids}}
        )
        res = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
        )
        out: list[RetrievalResult] = []
        ids = res.get("ids", [[]])[0]
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        distances = res.get("distances", [[]])[0]
        for i, chunk_id in enumerate(ids):
            m = metas[i] or {}
            out.append(
                RetrievalResult(
                    chunk_id=chunk_id,
                    document_id=m.get("document_id", ""),
                    text=docs[i],
                    page_num=int(m.get("page_num", 0) or 0),
                    filename=m.get("filename", ""),
                    distance=float(distances[i]) if i < len(distances) else 0.0,
                    has_associated_image=bool(m.get("has_associated_image", False)),
                    image_path=m.get("image_path") or None,
                    block_type=m.get("block_type", "text"),
                )
            )
        return out

    def delete_by_document_id(self, document_id: str) -> int:
        existing = self.collection.get(where={"document_id": document_id})
        count = len(existing.get("ids", []) or [])
        if count > 0:
            self.collection.delete(where={"document_id": document_id})
        return count

    def get_stats(self) -> dict:
        return {"total_chunks": self.collection.count(), "collection": COLLECTION_NAME}

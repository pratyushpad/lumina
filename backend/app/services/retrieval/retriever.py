from app.services.embedding.embedder import EmbeddingService
from app.services.vectorstore.chroma import RetrievalResult, VectorStore
from app.config import settings


class Retriever:
    def __init__(self):
        self.embedder = EmbeddingService.get()
        self.store = VectorStore.get()

    async def retrieve(self, query: str, document_ids: list[str]) -> list[RetrievalResult]:
        if not document_ids:
            return []
        q_vec = self.embedder.embed_query(query)
        return self.store.query(q_vec, document_ids, top_k=settings.TOP_K_RETRIEVAL)

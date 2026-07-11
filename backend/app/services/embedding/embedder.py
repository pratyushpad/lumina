"""Sentence-transformer embedding singleton."""
import logging
from typing import Optional

from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger("lumina.embedder")


class EmbeddingService:
    _instance: Optional["EmbeddingService"] = None

    def __init__(self):
        logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info("Embedder ready (dim=%d)", self.dimension)

    @classmethod
    def get(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def embed_texts(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        if not texts:
            return []
        vectors = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return vectors.tolist()

    def embed_query(self, query: str) -> list[float]:
        vec = self.model.encode(
            [query], normalize_embeddings=True, show_progress_bar=False, convert_to_numpy=True
        )
        return vec[0].tolist()

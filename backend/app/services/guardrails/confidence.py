"""Refusal gate: when retrieval confidence is low, say so instead of guessing.

The cross-encoder reranker's sigmoid-normalized top score is the confidence
signal. Below MIN_RERANK_SCORE the LLM is never called — the false-refusal and
false-answer rates at this threshold are measured in docs/eval.md (threshold
sweep over answerable + unanswerable eval questions).
"""
from app.config import settings
from app.services.retrieval.types import RetrievalResult

REFUSAL_MESSAGE = (
    "I couldn't find anything in your documents that answers this question. "
    "The retrieved passages scored too low to be trustworthy evidence, so rather "
    "than guess, I'm saying so. Try rephrasing, or upload a document that covers this topic."
)


def should_refuse(results: list[RetrievalResult]) -> bool:
    if not settings.GUARDRAIL_REFUSAL_ENABLED:
        return False
    if not results:
        return True
    return max(r.relevance_score for r in results) < settings.MIN_RERANK_SCORE

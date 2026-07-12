"""Heuristic prompt-injection scan over retrieved chunk text.

Uploaded documents are untrusted input that lands inside the LLM prompt. Flagged
chunks are not dropped (they may still contain the answer) — they are wrapped in
a warning delimiter by the prompt builder and marked in the trace.
"""
import re

_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"ignore\s+(all\s+|any\s+)?(previous|prior|above)\s+instructions",
        r"disregard\s+(all\s+|any\s+)?(previous|prior|above)",
        r"you\s+are\s+now\s+(a|an|no\s+longer)",
        r"system\s*prompt\s*[:=]",
        r"<\s*/?\s*system\s*>",
        r"\bDAN\b.{0,40}jailbreak|jailbreak.{0,40}\bDAN\b",
        r"do\s+not\s+(mention|reveal|tell)\s+.{0,40}(instructions|prompt)",
        # long base64-ish blobs (smuggled payloads)
        r"[A-Za-z0-9+/]{120,}={0,2}",
    )
]


def is_suspicious(text: str) -> bool:
    return any(p.search(text) for p in _PATTERNS)

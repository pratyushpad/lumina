"""Regex PII scrub applied at ingest when PII_SCRUB_ON_INGEST=true.

Deliberately simple (emails, phone numbers, SSNs, credit-card-shaped numbers);
regexes miss context-dependent PII like names and addresses — that limitation is
documented in the README. Off by default because it is lossy.
"""
import re

_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
    (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), "[CARD]"),
    (re.compile(r"(\+?\d{1,3}[ .-]?)?\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}\b"), "[PHONE]"),
]


def scrub(text: str) -> str:
    for pattern, token in _RULES:
        text = pattern.sub(token, text)
    return text

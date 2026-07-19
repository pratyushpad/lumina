#!/usr/bin/env python3
"""Fetch the arXiv papers used by the demo session and the eval corpus.

The PDFs are not committed to the repo: arXiv's perpetual non-exclusive license
grants distribution rights to arXiv, not to downstream repositories, so we pull
them from the source at setup/build time instead. SHA-256 of the copies the eval
set was frozen against are recorded below — a mismatch (arXiv occasionally
re-stamps PDFs) does not abort, but it is loudly reported because chunk ids
derive from file bytes and a changed corpus invalidates `eval/dataset.jsonl`.
"""
import hashlib
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAPERS = [
    # (arXiv id incl. version, destination, sha256 at freeze time)
    ("1706.03762v7", ROOT / "backend/demo_docs/attention-is-all-you-need.pdf",
     "bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697"),
    ("1512.03385v1", ROOT / "backend/demo_docs/resnet-deep-residual-learning.pdf",
     "1e0651b6810ecba34a3dbc5b5b0209226f889004607c1f203540a48d64e5a93a"),
    ("1706.03762v7", ROOT / "eval/corpus/attention_is_all_you_need.pdf",
     "bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697"),
    ("2005.11401v4", ROOT / "eval/corpus/rag_knowledge_intensive_nlp.pdf",
     "23e3249e9a1e75418d82efecab0ea8c4d033b89c93742f63208d47ce01f21233"),
]


def main() -> int:
    mismatches = 0
    for arxiv_id, dest, expected in PAPERS:
        if dest.exists():
            print(f"exists   {dest.relative_to(ROOT)}")
            continue
        url = f"https://export.arxiv.org/pdf/{arxiv_id}"
        print(f"fetching {dest.relative_to(ROOT)}  <-  {url}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "lumina-fetch/1.0"})
        data = urllib.request.urlopen(req, timeout=120).read()
        dest.write_bytes(data)
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            mismatches += 1
            print(f"  WARNING: sha256 mismatch for {dest.name}!\n"
                  f"    expected {expected}\n    got      {actual}\n"
                  f"    arXiv may have re-stamped the PDF. Chunk ids will differ from the\n"
                  f"    frozen eval set — eval/dataset.jsonl ground truth may not apply.")
    if mismatches:
        print(f"\n{mismatches} file(s) differ from the frozen copies (see warnings above).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

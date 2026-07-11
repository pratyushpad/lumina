"""Semantic chunker: recursive split preserving paragraph/sentence boundaries with overlap."""
from dataclasses import dataclass
from typing import Optional

from app.config import settings
from app.utils.text_utils import estimate_tokens


@dataclass
class ChunkData:
    chunk_id: str
    document_id: str
    text: str
    page_num: int
    chunk_index: int
    block_type: str
    char_count: int
    token_estimate: int
    filename: str
    has_associated_image: bool = False
    image_path: Optional[str] = None


class TextChunker:
    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    def chunk(
        self,
        text_blocks: list[dict],
        extracted_images: list[dict],
        document_id: str,
        filename: str,
    ) -> list[ChunkData]:
        out: list[ChunkData] = []
        idx = 0
        prev_tail = ""

        # Group blocks by page (preserve order)
        for block in text_blocks:
            text = block["text"]
            page_num = block["page_num"]
            block_type = block["block_type"]

            if block_type == "table":
                # Keep table as single chunk (do not split)
                chunk_text = text
                if prev_tail:
                    chunk_text = prev_tail + "\n\n" + chunk_text
                out.append(self._build_chunk(chunk_text, document_id, filename, page_num, idx, "table"))
                prev_tail = chunk_text[-self.chunk_overlap :]
                idx += 1
                continue

            # Recursive split for text blocks
            pieces = self._split_recursive(text, self.chunk_size)
            for piece in pieces:
                stripped = piece.strip()
                if len(stripped) < 50:
                    continue
                final_text = (prev_tail + "\n" + stripped) if prev_tail else stripped
                out.append(
                    self._build_chunk(final_text, document_id, filename, page_num, idx, "text")
                )
                prev_tail = final_text[-self.chunk_overlap :]
                idx += 1

        # Image-caption chunks
        for img in extracted_images:
            page_num = img["page_num"]
            text = f"[IMAGE on page {page_num} of {filename}] {img.get('caption', '')}".strip()
            out.append(
                ChunkData(
                    chunk_id=f"{document_id}_chunk_{idx}",
                    document_id=document_id,
                    text=text,
                    page_num=page_num,
                    chunk_index=idx,
                    block_type="image_caption",
                    char_count=len(text),
                    token_estimate=estimate_tokens(text),
                    filename=filename,
                    has_associated_image=True,
                    image_path=img["image_path"],
                )
            )
            idx += 1

        return out

    def _build_chunk(
        self, text: str, document_id: str, filename: str, page_num: int, idx: int, block_type: str
    ) -> ChunkData:
        return ChunkData(
            chunk_id=f"{document_id}_chunk_{idx}",
            document_id=document_id,
            text=text,
            page_num=page_num,
            chunk_index=idx,
            block_type=block_type,
            char_count=len(text),
            token_estimate=estimate_tokens(text),
            filename=filename,
        )

    def _split_recursive(self, text: str, size: int) -> list[str]:
        if len(text) <= size:
            return [text]
        # Try paragraph
        for sep in ["\n\n", "\n", ". "]:
            if sep in text:
                parts = text.split(sep)
                result: list[str] = []
                buf = ""
                for p in parts:
                    candidate = (buf + sep + p) if buf else p
                    if len(candidate) <= size:
                        buf = candidate
                    else:
                        if buf:
                            result.append(buf)
                        if len(p) > size:
                            result.extend(self._split_recursive(p, size))
                            buf = ""
                        else:
                            buf = p
                if buf:
                    result.append(buf)
                return result
        # Hard split with overlap
        result = []
        start = 0
        while start < len(text):
            end = min(start + size, len(text))
            result.append(text[start:end])
            if end >= len(text):
                break
            start = end - self.chunk_overlap
        return result

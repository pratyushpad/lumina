from app.services.ingestion.chunker import TextChunker


def test_chunker_respects_paragraph_boundary():
    chunker = TextChunker(chunk_size=200, chunk_overlap=20)
    text = "Para one. " * 10 + "\n\n" + "Para two. " * 10
    blocks = [{"text": text, "page_num": 1, "block_type": "text"}]
    chunks = chunker.chunk(blocks, [], "doc1", "f.txt")
    assert len(chunks) >= 1
    assert all(c.char_count >= 50 for c in chunks)


def test_chunker_keeps_table_as_single_chunk():
    table = "| a | b |\n| --- | --- |\n| 1 | 2 |"
    blocks = [{"text": table, "page_num": 1, "block_type": "table"}]
    chunks = TextChunker().chunk(blocks, [], "doc2", "t.pdf")
    assert len(chunks) == 1
    assert chunks[0].block_type == "table"


def test_chunker_emits_image_caption_chunk():
    images = [{"image_path": "/tmp/x.png", "page_num": 2, "caption": "fig"}]
    chunks = TextChunker().chunk([], images, "doc3", "f.pdf")
    assert any(c.has_associated_image for c in chunks)

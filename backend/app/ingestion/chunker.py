import tiktoken
from backend.app.config import CHUNK_SIZE, OVERLAP


def _page_for_offset(offset: int, boundaries: list) -> int:
    page = boundaries[0][1]
    for b_offset, pnum in boundaries:
        if b_offset <= offset:
            page = pnum
        else:
            break
    return page


def chunk_pages(pages: list[dict], chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[dict]:
    encoder = tiktoken.get_encoding("cl100k_base")

    full_text = ""
    page_boundaries = []
    for p in pages:
        page_boundaries.append((len(full_text), p["page"]))
        full_text += p["text"] + " "

    tokens = encoder.encode(full_text)
    chunks = []
    idx = 0
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_text = encoder.decode(tokens[start:end])
        char_offset = len(encoder.decode(tokens[:start]))
        page_num = _page_for_offset(char_offset, page_boundaries)
        chunks.append({"text": chunk_text.strip(), "page": page_num, "chunk_index": idx})
        idx += 1
        start += chunk_size - overlap
    return chunks


def chunk_text_simple(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[dict]:
    encoder = tiktoken.get_encoding("cl100k_base")
    tokens = encoder.encode(text)
    chunks, idx, start = [], 0, 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunks.append({"text": encoder.decode(tokens[start:end]).strip(), "page": None, "chunk_index": idx})
        idx += 1
        start += chunk_size - overlap
    return chunks
from backend.app.ingestion.document_parser import parse_document
from backend.app.ingestion.chunker import chunk_pages, chunk_text_simple
from backend.app.ingestion.web_loader import fetch_website_content
from backend.app.rag.vector_store import store_chunks
from backend.app.core.enums import SourceType, IngestionStatus


def ingest_source(source, tenant_id: str, agent_id: str) -> int:
    total_chunks = 0

    if source.source_type == SourceType.WEBSITE:
        pages = fetch_website_content(source.url, use_exa=True, discover_similar=False)
        chunk_offset = 0
        for web_page in pages:
            chunks = chunk_text_simple(web_page["text"])
            if not chunks:
                continue
            for c in chunks:
                c["chunk_index"] += chunk_offset
            total_chunks += store_chunks(tenant_id, agent_id, source.source_id, chunks)
            chunk_offset += len(chunks)
    else:
        pages = parse_document(source.file_path)
        if not pages:
            return 0
        chunks = chunk_pages(pages)
        if not chunks:
            return 0
        total_chunks = store_chunks(tenant_id, agent_id, source.source_id, chunks)

    return total_chunks


def process_source(source, tenant_id: str, agent_id: str) -> int:
    source.status = IngestionStatus.PROCESSING
    try:
        count = ingest_source(source, tenant_id, agent_id)
        source.status = IngestionStatus.READY
        return count
    except Exception as e:
        source.status = IngestionStatus.FAILED
        source.error = str(e)
        raise
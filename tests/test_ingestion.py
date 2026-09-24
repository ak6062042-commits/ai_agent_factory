from pathlib import Path

from backend.app.ingestion.chunker import chunk_text_simple
from backend.app.ingestion.document_parser import clean_text, parse_csv, parse_document
from backend.app.ingestion.web_loader import WebsiteFetchError, _is_safe_url, fetch_website_content
from backend.app.llm.prompt_generator import _fallback_prompt
from backend.app.rag.retriver import _unpack


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_text_cleanup_and_csv_parsing():
    file_path = FIXTURES_DIR / "sample.csv"

    assert clean_text("  Refund\n\n policy  ") == "Refund policy"
    assert parse_csv(str(file_path)) == [{"text": "topic: refunddetail: 30 days", "page": 1}]
    assert parse_document(str(file_path)) == [{"text": "topic: refunddetail: 30 days", "page": 1}]


def test_unsupported_document_type_raises_value_error():
    unsupported = FIXTURES_DIR / "guide.md"

    try:
        parse_document(str(unsupported))
    except ValueError as error:
        assert "Unsupported file type" in str(error)
    else:
        raise AssertionError("Unsupported formats must be rejected")


def test_chunking_assigns_sequential_indices():
    chunks = chunk_text_simple("word " * 30, chunk_size=10, overlap=2)

    assert [chunk["chunk_index"] for chunk in chunks] == list(range(len(chunks)))
    assert all(chunk["page"] is None for chunk in chunks)


def test_unsafe_urls_are_rejected_before_a_network_request():
    assert _is_safe_url("http://127.0.0.1/private") is False
    assert _is_safe_url("http://localhost/private") is False
    assert _is_safe_url("ftp://example.com/file") is False

    try:
        fetch_website_content("http://127.0.0.1/private")
    except WebsiteFetchError:
        pass
    else:
        raise AssertionError("Unsafe URLs must not be fetched")


def test_retrieval_unpacking_and_prompt_fallback():
    results = {
        "ids": [["chunk-1"]],
        "documents": [["refund policy"]],
        "metadatas": [[{"page": -1, "source_id": "source-1", "chunk_index": 0}]],
        "distances": [[0.2]],
    }

    assert _unpack(results) == [{
        "id": "chunk-1", "text": "refund policy", "page": None,
        "source_id": "source-1", "chunk_index": 0, "score": 0.2,
    }]
    assert "You are Support Bot" in _fallback_prompt("Support Bot")

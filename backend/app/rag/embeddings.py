from backend.app.llm.client import EmbeddingClient

_embedder = EmbeddingClient()


def embed_text(text: str) -> list[float]:
    return _embedder.embed(text)


def embed_texts(texts: list[str]) -> list[list[float]]:
    return _embedder.embed_batch(texts)
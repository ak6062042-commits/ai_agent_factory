from chromadb import PersistentClient
from backend.app.config import VECTOR_DB_PATH, COLLECTION_NAME
from backend.app.rag.embeddings import embed_texts
from chromadb.config import Settings


def get_collection():
    client = PersistentClient(path = VECTOR_DB_PATH, settings=Settings(anonymized_telemetry=False))
    return client.get_or_create_collection(name = COLLECTION_NAME, metadata = {"hnsw:space": "cosine"})


def store_chunks(tenant_id: str, agent_id: str, source_id: str, chunks: list[dict]) -> int:
    if not chunks:
        return 0

    collection = get_collection()
    texts = [c["text"] for c in chunks]
    ids = [f"{tenant_id}_{agent_id}_{source_id}_{c['chunk_index']}" for c in chunks]
    metadatas = [
        {
            "tenant_id": tenant_id,
            "agent_id": agent_id,
            "source_id": source_id,
            "page": c["page"] if c["page"] is not None else -1,
            "chunk_index": c["chunk_index"],
        }
        for c in chunks
    ]
    embeddings = embed_texts(texts)
    collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=texts)
    return len(chunks)

# Agent Deletion inspired by the other Intern's implementation 
def delete_agent_vectors(tenant_id : str, agent_id: str) -> None:
    collection = get_collection()
    collection.delete(where = {"$and": [{"tenant_id": tenant_id, "agent_id": agent_id}]})
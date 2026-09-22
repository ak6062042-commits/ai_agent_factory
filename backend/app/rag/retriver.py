from backend.app.rag.vector_store import get_collection
from backend.app.rag.embeddings import embed_text


def retrieve(tenant_id: str, agent_id: str, query: str, top_k: int = 5) -> list[dict]:
    if not query or not query.strip():
        return []

    collection = get_collection()
    query_embedding = embed_text(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"$and": [{"tenant_id": tenant_id}, {"agent_id": agent_id}]},
    )
    return _unpack(results)


def _unpack(results) -> list[dict]:
    found = []
    if not results["ids"] or not results["ids"][0]:
        return found

    ids = results["ids"][0]
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    for i in range(len(ids)):
        page = metas[i].get("page")
        found.append({
            "id": ids[i],
            "text": docs[i],
            "page": None if page == -1 else page,
            "source_id": metas[i].get("source_id"),
            "score": dists[i],
        })
    return found
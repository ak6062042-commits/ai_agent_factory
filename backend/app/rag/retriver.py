from backend.app.rag.vector_store import get_collection
from backend.app.rag.embeddings import embed_text
from backend.app.config import SIMILARITY_THRESHOLD

# TODO: SIMILARITY THRESHOLD IS JUST A PLACE HOLDER IN config RIGHT figure out a good sweet spot after tests
def retrieve(tenant_id: str, agent_id: str, query: str, top_k: int = 5, max_distance: float = SIMILARITY_THRESHOLD) -> list[dict]:
    if not query or not query.strip():
        return []

    collection = get_collection()
    query_embedding = embed_text(query)

    results = collection.query(query_embeddings = [query_embedding], n_results = top_k,where = {"$and": [{"tenant_id": tenant_id}, {"agent_id": agent_id}]},)
    unpacked = _unpack(results)
    
    return [r for r in unpacked if r["score"] <= max_distance] 
    


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
            "chunk_index": metas[i].get("chunk_index"),
            "score": dists[i]
        })
    return found
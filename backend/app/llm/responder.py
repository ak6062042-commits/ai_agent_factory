from backend.app.llm.client import LLMClient
from backend.app.rag.retriver import retrieve


def build_answer(tenant_id: str, agent_id: str, system_prompt: str, conversation_history: str, question: str) -> tuple[str, list[dict]]:
    retrieved = retrieve(tenant_id, agent_id, question, top_k=5)  # used SIMILARITY_THRESHOLD = 0.65 default

    if not retrieved:
        return (
            "I cannot find that in the provided information.",
            [],
        )

    context_block = "\n---\n".join(r["text"] for r in retrieved)

    messages = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        messages.append({"role": "system", "content": f"Recent conversation:\n{conversation_history}"})
    messages.append({"role": "user", "content": f"Context:\n{context_block}\n\nQuestion: {question}"})

    answer = LLMClient().generate(messages)

    citations = [
        {"source_id": r["source_id"], "page": r.get("page")}
        for r in retrieved
    ]
    return answer, citations

# SERIOUS NOTE: """citations here returns source_id, not the full title/source_type/url your 
# Citation schema needs — that mapping (source_id → title/type/url) requires a Source lookup, 
# which belongs in chat_services.py since it's DB-aware and responder.py deliberately isn't 
# (keeps this file able to be tested/reasoned about without a DB session)."""
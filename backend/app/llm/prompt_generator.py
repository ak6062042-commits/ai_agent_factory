from backend.app.llm.client import LLMClient
from backend.app.rag.retriver import retrieve

GENERAL_PROMPT = """You are a hybrid AI assistant combining the conversational fluency of top-tier chat models with absolute factual precision. 
Base your answers strictly on the provided context. 
If the answer cannot be found in the context, say 'I cannot find that in the provided information'—do not extrapolate or assume.
Keep your tone engaging, clear, and direct."""

_SAMPLE_QUERY = "What topics, facts, and information does this knowledge base cover?"


def generate_system_prompt(tenant_id: str, agent_id: str, agent_name: str) -> str:
    """
    Builds a per-agent system prompt: GENERAL_PROMPT (fixed behavior rules)
    + an LLM-written summary of what this agent's ingested knowledge covers.
    Falls back to a safe generic prompt if retrieval/generation fails or
    returns nothing (e.g. ingestion succeeded but content was extremely sparse).
    """
    sample_chunks = retrieve(tenant_id, agent_id, _SAMPLE_QUERY, top_k=10, max_distance=999.9)

    if not sample_chunks:
        return _fallback_prompt(agent_name)

    knowledge_excerpt = "\n---\n".join(c["text"] for c in sample_chunks)

    summarizer_messages = [
        {"role": "system", "content": (
            "You write a short (2-4 sentence) description of what a knowledge base "
            "covers, based on sample excerpts from it. Be specific about topics and "
            "scope. Do not answer questions, just describe the domain/content."
        )},
        {"role": "user", "content": f"Sample excerpts:\n\n{knowledge_excerpt}\n\nDescribe what this knowledge base covers."},
    ]

    try:
        knowledge_summary = LLMClient().generate(summarizer_messages)
    except Exception:
        return _fallback_prompt(agent_name)

    return (
        f"{GENERAL_PROMPT}\n\n"
        f"You are {agent_name}. Your knowledge base covers: {knowledge_summary}\n"
        f"Only answer using the context provided to you for each question."
    )


def _fallback_prompt(agent_name: str) -> str:
    return (
        f"{GENERAL_PROMPT}\n\n"
        f"You are {agent_name}, an AI assistant. Answer questions using only "
        f"the knowledge provided in context. If the answer isn't there, say so."
    )
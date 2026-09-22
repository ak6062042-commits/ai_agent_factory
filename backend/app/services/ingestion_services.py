from backend.app.ingestion.pipeline import process_source
from backend.app.core.enums import IngestionStatus
from backend.app.db.database import get_session
from backend.app.db import repositories


def run_ingestion(agent_id: str) -> None:
    with get_session() as session:
        agent = repositories.get_agent_by_id_unscoped(session, agent_id)
        if agent is None:
            return

        total_chunks = 0
        any_success = False

        for source in agent.sources:
            try:
                total_chunks += process_source(source, agent.tenant_id, agent.agent_id)
                any_success = True
            except Exception:
                pass  

        agent.indexed_chunk_count = total_chunks

        if any_success:
            agent.ingestion_status = IngestionStatus.READY
            agent.system_prompt = _build_placeholder_prompt(agent)
        else:
            agent.ingestion_status = IngestionStatus.FAILED
            agent.failure_reason = "All sources failed to ingest"


def _build_placeholder_prompt(agent) -> str:
    return (
        f"You are {agent.agent_name}, an AI assistant. Answer questions using "
        f"only the knowledge provided. If the answer isn't in your knowledge "
        f"base, say you don't know."
    )
from sqlalchemy.orm import Session

from backend.app.db import repositories
from backend.app.core.enums import Roles
from backend.app.llm.responder import build_answer
from backend.app.rag.history import History
from backend.app.schemas.chat import ChatResponse, Citation

_history = History()  # module-level singleton; in-memory


def handle_chat(db: Session, tenant_id: str, agent, session_id: str, message: str) -> ChatResponse:
    agent_id = agent.agent_id

    convo = repositories.get_or_create_conversation(db, tenant_id, agent_id, session_id)

    conversation_string = _history.build_conversation_string(tenant_id, agent_id, session_id)

    answer, raw_citations = build_answer(
        tenant_id=tenant_id,
        agent_id=agent_id,
        system_prompt=agent.system_prompt or "",
        conversation_history=conversation_string,
        question=message,
    )

    citations = _resolve_citations(db, tenant_id, agent_id, raw_citations)

    repositories.create_message(db, tenant_id, agent_id, convo.conversation_id, Roles.USER, message)
    repositories.create_message(
        db, tenant_id, agent_id, convo.conversation_id, Roles.ASSISTANT, answer,
        citation=[c.model_dump(mode="json") for c in citations],
    )
    db.commit()

    _history.add_message(tenant_id, agent_id, session_id, "user", message)
    _history.add_message(tenant_id, agent_id, session_id, "assistant", answer)

    return ChatResponse(session_id=session_id, answer=answer, sources=citations)


def _resolve_citations(db: Session, tenant_id: str, agent_id: str, raw_citations: list[dict]) -> list[Citation]:
    citations = []
    seen_source_ids = set()
    for rc in raw_citations:
        source_id = rc.get("source_id")
        if not source_id or source_id in seen_source_ids:
            continue
        seen_source_ids.add(source_id)

        source = repositories.get_source_by_id(db, tenant_id, agent_id, source_id)
        if not source:
            continue

        citations.append(Citation(
            source_type=source.source_type,
            title=source.title,
            page=rc.get("page"),
            url=source.url,
        ))
    return citations
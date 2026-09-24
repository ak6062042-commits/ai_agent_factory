from backend.app.core.enums import Roles, SourceType
from backend.app.db import repositories
from backend.app.db.models import Source
from backend.app.services import chat_services

from conftest import make_agent


def test_handle_chat_persists_messages_and_resolves_unique_citations(monkeypatch, session, tenant):
    agent = make_agent(tenant.tenant_id, system_prompt="Use context")
    session.add(agent)
    session.commit()
    source = Source(
        tenant_id=tenant.tenant_id,
        agent_id=agent.agent_id,
        source_type=SourceType.DOCUMENT,
        title="handbook.pdf",
    )
    session.add(source)
    session.commit()
    chat_services._history.chat_sessions.clear()
    monkeypatch.setattr(
        chat_services,
        "build_answer",
        lambda **kwargs: ("Refunds are available.", [{"source_id": source.source_id, "page": 3}, {"source_id": source.source_id, "page": 3}]),
    )

    response = chat_services.handle_chat(session, tenant.tenant_id, agent, "session-1", "What is the refund policy?")

    messages = repositories.get_recent_messages(
        session, tenant.tenant_id, agent.agent_id,
        repositories.get_or_create_conversation(session, tenant.tenant_id, agent.agent_id, "session-1").conversation_id,
    )
    assert response.answer == "Refunds are available."
    assert response.session_id == "session-1"
    assert len(response.sources) == 1
    assert response.sources[0].title == "handbook.pdf"
    assert [message.role for message in messages] == [Roles.USER, Roles.ASSISTANT]
    assert messages[1].citation == [{"source_type": "document", "title": "handbook.pdf", "page": 3, "url": None}]


def test_handle_chat_ignores_citations_that_do_not_belong_to_agent(monkeypatch, session, tenant):
    agent = make_agent(tenant.tenant_id)
    session.add(agent)
    session.commit()
    chat_services._history.chat_sessions.clear()
    monkeypatch.setattr(
        chat_services,
        "build_answer",
        lambda **kwargs: ("Answer", [{"source_id": "unknown", "page": None}]),
    )

    response = chat_services.handle_chat(session, tenant.tenant_id, agent, "session-2", "Question")

    assert response.sources == []


def test_smalltalk_detection_and_grounding_refusal_do_not_need_an_llm(monkeypatch):
    from backend.app.llm import responder

    assert responder._is_smalltalk("Thanks!") is True
    assert responder._is_smalltalk("What is the refund policy?") is False
    monkeypatch.setattr(responder, "retrieve", lambda *args, **kwargs: [])

    answer, citations = responder.build_answer("tenant", "agent", "prompt", "", "What is the refund policy?")

    assert answer == "I cannot find that in the provided information."
    assert citations == []

from backend.app.db import repositories

from conftest import make_agent, make_tenant


def test_agents_are_listed_only_for_their_tenant(session):
    first = make_tenant()
    second = make_tenant(admin_email="second@acme.example", hashed_api_key="hash-2")
    session.add_all([first, second])
    session.commit()
    first_agent = make_agent(first.tenant_id)
    second_agent = make_agent(second.tenant_id, agent_name="Second Bot")
    session.add_all([first_agent, second_agent])
    session.commit()

    assert [agent.agent_id for agent in repositories.get_agents_for_tenant(session, first.tenant_id)] == [first_agent.agent_id]
    assert repositories.get_agent_by_id(session, first.tenant_id, second_agent.agent_id) is None


def test_conversations_with_the_same_session_are_isolated_by_tenant_and_agent(session):
    first = make_tenant()
    second = make_tenant(admin_email="second@acme.example", hashed_api_key="hash-2")
    session.add_all([first, second])
    session.commit()
    first_agent = make_agent(first.tenant_id)
    second_agent = make_agent(second.tenant_id)
    session.add_all([first_agent, second_agent])
    session.commit()

    first_conversation = repositories.get_or_create_conversation(session, first.tenant_id, first_agent.agent_id, "shared")
    second_conversation = repositories.get_or_create_conversation(session, second.tenant_id, second_agent.agent_id, "shared")

    assert first_conversation.conversation_id != second_conversation.conversation_id
    assert repositories.get_or_create_conversation(session, first.tenant_id, first_agent.agent_id, "shared").conversation_id == first_conversation.conversation_id

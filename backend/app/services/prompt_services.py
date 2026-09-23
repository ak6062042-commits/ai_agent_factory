from sqlalchemy.orm import Session

from backend.app.llm.prompt_generator import generate_system_prompt


def generate_and_store_prompt(db: Session, agent) -> None:
    """
    Generates a knowledge-grounded system prompt for `agent` and sets it
    on the ORM object. Caller (ingestion_services) owns the commit —
    this function only mutates, per the project's transaction-boundary rule.
    """
    agent.system_prompt = generate_system_prompt(
        tenant_id=agent.tenant_id,
        agent_id=agent.agent_id,
        agent_name=agent.agent_name,
    )
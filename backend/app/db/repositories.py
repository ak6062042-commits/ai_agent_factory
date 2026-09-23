from backend.app.db.models import Tenant
from typing import Optional
from sqlalchemy.orm import Session
from backend.app.db.models import Agent, Source
from backend.app.core.enums import SourceType
from backend.log.logger import Logger

logger = Logger()

def create_tenant(db: Session, organization_name: str, admin_email: str, hashed_api_key: str) -> Tenant:
    normalized_email = admin_email.strip().lower()
    tenant = Tenant(organization_name = organization_name, admin_email = normalized_email, hashed_api_key = hashed_api_key)
    db.add(tenant)
    db.flush()
    
    return tenant

def get_tenant_by_api_key_hash(db: Session, hashed_key: str) -> Optional[Tenant]:
    return db.query(Tenant).filter(Tenant.hashed_api_key == hashed_key).first()

def get_tenant_by_id(db: Session, tenant_id) -> Optional[Tenant]:
    return db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()


def create_agent(db: Session, tenant_id: str, agent_name: str, website_url: str) -> Agent:
    agent = Agent(tenant_id=tenant_id, agent_name=agent_name, website_url=website_url)
    db.add(agent)
    db.flush()
    return agent


def get_agent_by_id(db: Session, tenant_id: str, agent_id: str) -> Optional[Agent]:
    return (db.query(Agent).filter(Agent.tenant_id == tenant_id, Agent.agent_id == agent_id).first())


def get_agent_by_id_unscoped(db: Session, agent_id: str) -> Optional[Agent]:
    return db.query(Agent).filter(Agent.agent_id == agent_id).first()


def get_agents_for_tenant(db: Session, tenant_id: str) -> list[Agent]:
    return db.query(Agent).filter(Agent.tenant_id == tenant_id).all()


def create_source(db: Session, tenant_id: str, agent_id: str,source_type: SourceType, title: str, url: Optional[str] = None,file_path: Optional[str] = None) -> Source:
    source = Source(
        tenant_id=tenant_id, agent_id=agent_id,
        source_type=source_type, title=title, url=url, file_path=file_path,
    )
    db.add(source)
    db.flush()
    return source

# The real Last minute change

def delete_agent(db: Session, tenant_id: str, agent_id: str):
    agent = get_agent_by_id(db, tenant_id = tenant_id, agent_id = agent_id)
    
    if not agent:
        logger.log(f"NO agent with the provided agent_id: ({agent_id}) found aborting deletion", "WARNING")
        return False
    db.delete(agent)
    logger.log(F"Agent with the provided agent_id: ({agent_id}) deleted", "INFO")
    return True
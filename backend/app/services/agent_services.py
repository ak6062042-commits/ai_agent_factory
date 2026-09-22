import asyncio
from datetime import datetime, timezone
from fastapi import UploadFile
from sqlalchemy.orm import Session
from backend.app.core.enums import IngestionStatus, SourceType
from backend.app.db import repositories
from backend.app.db.database import get_session
from backend.app.db.models import Tenant
from backend.app.schemas.agent import AgentResponse
from backend.app.storage.file_storage import save_upload
from typing import List

def create_agent(db: Session, tenant: Tenant, agent_name: str, website_url: str, document: List[UploadFile]) -> AgentResponse:
    agent = repositories.create_agent(db, tenant_id = tenant.tenant_id, website_url = website_url, agent_name = agent_name)
    db.commit()
    db.refresh(agent)
    
    for docs in document:
        save_upload(tenant_id = tenant.tenant_id, agent_id = agent.agent_id, uploaded_file = docs)
        repositories.create_source(db, tenant_id = tenant.tenant_id, agent_id = agent.agent_id, source_type = SourceType.DOCUMENT, title = docs.filename, url = None)
    
    repositories.create_source(db, tenant_id = tenant.tenant_id, agent_id = agent.agent_id, source_type = SourceType.WEBSITE, title = website_url, url = website_url)
    
    db.commit()
    
    # asyncio.create_task(_run_ingestion_stub(agent.agent_id))
    return AgentResponse.model_validate(agent)

async def _run_ingestion_stub(agent_id: str):
    # Ingestion service place holder
    
    await asyncio.sleep(3)
    
    with get_session() as session:
        agent = repositories.get_agent_by_id_unscoped(session, agent_id)
        if agent is None:
            return
        
        agent.ingestion_status = IngestionStatus.READY
        agent.system_prompt = ""
        agent.indexed_chunk_count = 0

from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session

from backend.app.core.enums import SourceType
from backend.app.db import repositories
from backend.app.schemas.agent import AgentResponse
from backend.app.storage.file_storage import save_upload
from backend.app.db.models import Tenant
from backend.app.services.ingestion_services import run_ingestion
from backend.app.rag import vector_store
from backend.app.storage import file_storage
from backend.app.ingestion.pipeline import process_source
from backend.app.core.enums import SourceType


def create_agent(db: Session, tenant: Tenant, agent_name: str, website_url: str, documents: List[UploadFile], background_tasks  ) -> AgentResponse:
    agent = repositories.create_agent(db, tenant_id = tenant.tenant_id, agent_name = agent_name, website_url = website_url)
    db.commit()
    db.refresh(agent)

    for doc in documents:
        file_path = save_upload(tenant.tenant_id, agent.agent_id, doc)
        repositories.create_source(db, tenant_id = tenant.tenant_id, agent_id = agent.agent_id, source_type = SourceType.DOCUMENT, title = doc.filename, url = None, file_path = file_path)
        
    repositories.create_source(db, tenant_id = tenant.tenant_id, agent_id = agent.agent_id, source_type = SourceType.WEBSITE, title = website_url, url = website_url,)
    db.commit()
    db.refresh(agent)
    background_tasks.add_task(run_ingestion, agent.agent_id)

    return AgentResponse.model_validate(agent)

def delete_agent(db: Session, tenant_id: str, agent_id: str):
    agent = repositories.get_agent_by_id(db, tenant_id = tenant_id, agent_id = agent_id)
    if not agent:
        return False
    
    vector_store.delete_agent_vectors(tenant_id, agent_id)
    file_storage.delete_agent_files(tenant_id, agent_id)
    deleted = repositories.delete_agent(db, tenant_id = tenant_id, agent_id = agent_id)
    db.commit()
    
    return deleted


def add_source(db: Session, tenant_id: str, agent_id: str, website_url: Optional[str], document: Optional[UploadFile]) -> Source:
    agent = repositories.get_agent_by_id(db, tenant_id, agent_id)
    if not agent:
        return None

    if document is not None:
        file_path = save_upload(tenant_id, agent_id, document)
        source = repositories.create_source(
            db, tenant_id=tenant_id, agent_id=agent_id,
            source_type=SourceType.DOCUMENT, title=document.filename, url=None, file_path=file_path
        )
    elif website_url:
        source = repositories.create_source(
            db, tenant_id=tenant_id, agent_id=agent_id,
            source_type=SourceType.WEBSITE, title=str(website_url), url=str(website_url), file_path=None
        )
    else:
        return None  

    db.commit()
    db.refresh(source)

    try:
        chunk_count = process_source(source, tenant_id, agent_id)
        agent.indexed_chunk_count += chunk_count
        db.commit()
    except Exception:
        db.commit()  
    return source


def delete_source(db: Session, tenant_id: str, agent_id: str, source_id: str) -> bool:
    source = repositories.get_source_by_id(db, tenant_id, agent_id, source_id)
    if not source:
        return False

    vector_store.delete_source_vectors(tenant_id, agent_id, source_id)
    file_storage.delete_source_file(source.file_path)

    deleted = repositories.delete_source(db, tenant_id, agent_id, source_id)
    db.commit()
    return deleted
    
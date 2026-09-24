from fastapi import APIRouter, Depends, Form, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from backend.app.config import MAX_UPLOADS
from backend.app.core.security import get_current_tenant
from backend.app.db.database import get_db
from backend.app.db.models import Tenant
from backend.app.db import repositories
from backend.app.schemas.agent import AgentResponse
from backend.app.services import agent_services
from pydantic import AnyHttpUrl, ValidationError

from fastapi import Form, File, UploadFile
from typing import Optional
from pydantic import AnyHttpUrl, ValidationError
from backend.app.schemas.agent import AgentSource

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=AgentResponse, status_code=201)
def create_agent(background_tasks: BackgroundTasks, agent_name: str = Form(...), website_url: str = Form(...), documents: List[UploadFile] = File(...), db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant),):
    if len(documents) > MAX_UPLOADS:
        raise HTTPException(status_code=400, detail=f"Too many files: max {MAX_UPLOADS}, got {len(documents)}")
    agent_name = agent_name.strip()
    if not agent_name:
        raise HTTPException(status_code = 422, detail = "agent_name must not be empty")
    try:
        validate_url = str(AnyHttpUrl(website_url))
    except ValidationError as e:
        # I should probably log here
        raise HTTPException(status_code = 422, detail = "website url must be a valid http/https URL")
        
    
    return agent_services.create_agent(db, tenant, agent_name, validate_url, documents, background_tasks)


@router.get("", response_model=list[AgentResponse])
def list_agents(db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant)):
    return repositories.get_agents_for_tenant(db, tenant.tenant_id)


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: str, db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant)):
    agent = repositories.get_agent_by_id(db, tenant.tenant_id, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.delete("/{agent_id}", status_code = 204)
def delete_agent(agent_id: str, tenant = Depends(get_current_tenant), db = Depends(get_db)):
    deleted = agent_services.delete_agent(db = db, tenant_id = tenant.tenant_id, agent_id = agent_id)
    if not deleted:
        raise HTTPException(status_code = 404, detail = "Agent not found")



@router.post("/{agent_id}/sources", response_model=AgentSource, status_code=201)
def add_source(agent_id: str, website_url: Optional[str] = Form(None), document: Optional[UploadFile] = File(None), db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant),):
    validated_url = None
    if website_url:
        try:
            validated_url = AnyHttpUrl(website_url)
        except ValidationError:
            raise HTTPException(status_code=422, detail="website_url must be a valid http/https URL")

    if not validated_url and document is None:
        raise HTTPException(status_code=400, detail="Provide a website_url, a document, or both")

    source = agent_services.add_source(db, tenant.tenant_id, agent_id, validated_url, document)
    if source is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return source


@router.delete("/{agent_id}/sources/{source_id}", status_code=204)
def delete_source(agent_id: str, source_id: str, db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant)):
    deleted = agent_services.delete_source(db, tenant.tenant_id, agent_id, source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Source not found")
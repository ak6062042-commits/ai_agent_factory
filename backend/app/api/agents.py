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

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=AgentResponse, status_code=201)
def create_agent(
    background_tasks: BackgroundTasks,
    agent_name: str = Form(...),
    website_url: str = Form(...),
    documents: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    if len(documents) > MAX_UPLOADS:
        raise HTTPException(status_code=400, detail=f"Too many files: max {MAX_UPLOADS}, got {len(documents)}")
    return agent_services.create_agent(db, tenant, agent_name, website_url, documents, background_tasks)


@router.get("", response_model=list[AgentResponse])
def list_agents(db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant)):
    return repositories.get_agents_for_tenant(db, tenant.tenant_id)


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: str, db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant)):
    agent = repositories.get_agent_by_id(db, tenant.tenant_id, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
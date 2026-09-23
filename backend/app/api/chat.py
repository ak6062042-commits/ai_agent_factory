from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_tenant
from backend.app.db.database import get_db
from backend.app.db.models import Tenant
from backend.app.db import repositories
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.chat_services import handle_chat

router = APIRouter(prefix="/agents", tags=["chat"])


@router.post("/{agent_id}/chat", response_model=ChatResponse)
def chat(agent_id: str, request: ChatRequest, db: Session = Depends(get_db), tenant: Tenant = Depends(get_current_tenant)):
    agent = repositories.get_agent_by_id(db, tenant.tenant_id, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.ingestion_status.value != "ready":
        raise HTTPException(status_code=409, detail=f"Agent is not ready (status: {agent.ingestion_status.value})")

    return handle_chat(db=db, tenant_id=tenant.tenant_id, agent=agent, session_id=request.session_id, message=request.message)
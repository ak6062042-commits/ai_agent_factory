from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.schemas.tenant import TenantRequest, TenantResposne
from backend.app.services import tenant_services
from backend.log.logger import Logger

logger = Logger()

router = APIRouter(prefix = "/tenants", tags = ["tenants"])

@router.post("", response_model = TenantResposne, status_code = 201)
def create_tenant(payload: TenantRequest, db: Session = Depends(get_db)):
    try:
        return tenant_services.create_tenant(db, payload)
    except tenant_services.TenantAlreadyExistsError as e:
        raise HTTPException(status_code = 409, detail = str(e))
        
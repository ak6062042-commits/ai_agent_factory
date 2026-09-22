from backend.app.db.models import Tenant
from typing import Optional
from sqlalchemy.orm import Session
from backend.app.db.models import Agent, Source
from backend.app.core.enums import SourceType

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



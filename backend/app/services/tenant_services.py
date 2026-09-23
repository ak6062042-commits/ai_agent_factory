from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.app.core import security
from backend.app.db import repositories
from backend.app.schemas.tenant import TenantRequest, TenantResposne
from backend.log.logger import Logger
from datetime import datetime, timezone

logger = Logger()

class TenantAlreadyExistsError(Exception):
    pass

def create_tenant(db: Session, payload: TenantRequest):
    api_key = security.generate_api_key()
    hashed_api_key = security.hash_api_key(api_key)
    
    try:
        tenant = repositories.create_tenant(db, organization_name = payload.organization_name, admin_email = payload.admin_email.lower().strip(), hashed_api_key = hashed_api_key)
        db.commit()
    
    except IntegrityError:
        db.rollback()
        logger.log(f"A tenant already exists with this email{payload.admin_email}", "ERROR")
        raise TenantAlreadyExistsError("A tenant with this email already exists")
    db.refresh(tenant)
    
    return TenantResposne(
        tenant_id = tenant.tenant_id, 
        organization_name = tenant.organization_name, 
        admin_email = tenant.admin_email, 
        api_key = api_key, 
    )

# ================================================== THIS IS FOR ME DO NOT LOOK BEYOND IT WILL DELETE LATER ================================================== 

# To be NOTED tenant schema was this why a hashed key instead of the raw one
# class TenantResposne(BaseModel):
#     tenant_id: str
#     organization_name: str
#     admin_email: EmailStr
#     hashed_api_key: str
#     created_at: Optional[datetime] = None

# To be NOTED tenant db model is as follows 
# class Tenant(Base):
#     __tablename__ = "tenants"

#     tenant_id: Mapped[str] = mapped_column(primary_key = True, default = lambda: str(uuid.uuid4()))

#     organization_name: Mapped[str] = mapped_column(String)
#     # TODO = Email casing: the unique constraint treats A@x.com and a@x.com as different. Lowercase the email in the tenant service
#     admin_email: Mapped[str] = mapped_column(unique = True)
#     hashed_api_key: Mapped[str] = mapped_column(unique = True)

#     agents: Mapped[List["Agent"]] = relationship(back_populates = "tenant", cascade = "all, delete-orphan", passive_deletes = True) 
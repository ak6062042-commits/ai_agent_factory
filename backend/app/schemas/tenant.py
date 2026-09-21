from pydantic import BaseModel, Field, EmailStr, ConfigDict
from email_validator import validate_email, EmailNotValidError
from backend.log.logger import Logger


# NOTE: Not needed here but still wannna keep it (Looks good)
def isValidEmail(email: str) -> bool:
    try:
        email_info = validate_email(email, check_deliverability=True)
        normalized = email_info.email
        print(f"email validated* {normalized}")
        return True
    
    except EmailNotValidError as e:
        logger = Logger()
        logger.log(e, "ERROR")
        return False

class TenantRequest(BaseModel):
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    organization_name: str = Field(..., min_length=1, max_length = 50, description="Tenant's organization name")
    admin_email: EmailStr = Field(..., description="Tenant admin mail")

class TenantResposne(BaseModel):
    tenant_id: str
    organization_name: str
    admin_email: str
    api_key: str

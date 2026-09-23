class DesiredApproach:
    # NOTE: NO NEED FOR THIS CLASS IT IS HERE JUST FOR MY SELF SATISFACTION (will delete it someday when I feel like it)
    def __init__(self):
        pass
        
    def generate_api_key(self, admin_email: str, company_name: str) -> str:
        from cryptography.fernet import Fernet
        from backend.app.config import MASTER_KEY
        import json
        from datetime import datetime, timezone
        import base64
        
        cipher = Fernet(MASTER_KEY)
    
        payload = {
            "email": admin_email.lower(),
            "company_name": company_name.strip(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
        json_bytes = json.dumps(payload).encode('utf-8')
        encrypted_bytes = cipher.encrypt(json_bytes)
        generated_api_key = base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
    
        return generated_api_key

    def hash_api_key(self, api_key: str) -> str:
        import hashlib
        cleaned_api_key = api_key.strip()
        hash = hashlib.sha256(cleaned_api_key.encode('utf-8'))
        hashed_api_key = hash.hexdigest()
        return hashed_api_key


import secrets
import hashlib
from backend.app.db.models import Tenant
from fastapi import Header, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.repositories import get_tenant_by_api_key_hash
from backend.app.db.database import get_db
from backend.log.logger import Logger

logger = Logger()


def generate_api_key() -> str:
    return f"tsk_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    cleaned = api_key.strip()
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()

def get_current_tenant(db: Session = Depends(get_db), x_api_key: str = Header(...)) -> Tenant:   
    hashed = hash_api_key(x_api_key)
    tenant = get_tenant_by_api_key_hash(db, hashed)
    
    if tenant is None:
        logger.log(f"Invalid api key: {x_api_key}, a HTTPException with status code code 401 passed", "WARNING")
        raise HTTPException(status_code = 401, detail = "Invalid Api key")
    return tenant

if __name__ =="__main__":
    # client_email = "developer@acme.com"
    # client_company = "Acme Corp"

    new_api_key = generate_api_key()
    print(f"Generated API Key:\n{new_api_key}\n")
    
    hashed_api_key = hash_api_key(new_api_key)
    print(f" Hashed API Key:\n{hashed_api_key}\n")
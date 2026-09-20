from pydantic import BaseModel, Field, AnyHttpUrl, validator
from typing import Optional
from backend.log.logger import Logger
import os

logger = Logger()
ALLOWED_EXTENSIONS = [".pdf", ".txt", ".doc", ".docx"]

"""In FastAPI files are sent as multipart form data rather than standard JSON fields. 
We can use standard types or a custom field validator to enforce 
specific file extensions (.pdf, .doc, .docx, .txt)."""
# NOTE: Look into this more, I am implementing it according to theory but something still feels of!
class DocumentSchema(BaseModel):
    filename: str
    
    @validator(filename)
    def validate_file_extension(cls, value: str):
        _, extension = os.path.splitext(value.lower())
        
        if not extension in ALLOWED_EXTENSIONS:
            logger.log(f"Unspported file type {extension}", "ERROR")
            raise ValueError(f"Unspported file type {extension}")
        
        return value
    
    

class AgentRequest(BaseModel):
    document: Optional[DocumentSchema] = None
    url: AnyHttpUrl = Field(..., min_length = 7, max_length =  2048, description = "Tenant's web link to retrive data from")
    apiKey: str = Field(..., min_length = 1, description = "Tenant provided api_key", ) # api key was generated or rather will be generated after successfull tenant request

class AgentResponse(BaseModel): # I think it should responed with the access to chat let's figure it out
    pass

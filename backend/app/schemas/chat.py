from pydantic import BaseModel, Field, AnyHttpUrl, ConfigDict
from typing import Optional

from backend.app.core.enums import SourceType

class ChatRequest(BaseModel):
    
    model_config = ConfigDict(str_strip_whitespace = True)
    message: str = Field(..., min_length = 1, max_length = 10000, description = "User/Tenant's message/Prompt")
    session_id: str = Field(..., min_length = 1, description = "Unique id for the chat session")
    

class Citation(BaseModel):
    source_type: SourceType
    title: str
    page: Optional[int] = None
    url: Optional[AnyHttpUrl] = None

# the chat response can be from any of the cited meaning the response can be from the provide doc or from the website 
    

class ChatResponse(BaseModel):
    answer: str
    sources: list[Citation] = Field(default_factory = list)
    session_id: str

from pydantic import BaseModel, Field, AnyHttpUrl
from typing import Optional

class ChatRequest(BaseModel):
    message: str = Field(..., min_length = 1, description = "User/Tenant's message/Prompt")
    session_id: str = Field(..., min_length = 1, description = "Unique id for the chat session")

class Source(BaseModel):
    pdfTitle: str
    page: Optional[int] = None
    websiteTitle: Optional[str] = None
    url: AnyHttpUrl
    

class ChatResposne(BaseModel):
    answer: str
    source: list[Source] = Field(default_factory = list)

class Health(BaseModel):
    status: str
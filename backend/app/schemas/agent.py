from backend.app.core.enums import IngestionStatus, SourceType
from datetime import datetime
from pydantic import BaseModel, Field, AnyHttpUrl, ConfigDict
from typing import Optional


class CreateAgent(BaseModel):
    model_config = ConfigDict(str_strip_whitespace = True)
    agent_name: str = Field(..., min_length = 1, description = "Name of the AI agent")
    website_url: AnyHttpUrl = Field(..., min_length = 7, max_length = 2048, description = "Website URL ingested in the agents knowledge base" )

class AgentSource(BaseModel):
    
    model_config = ConfigDict(str_strip_whitespace = True)
    source_type: SourceType
    page: Optional[int] = None
    title: str
    url: Optional[AnyHttpUrl] = None
    status: IngestionStatus
    error: Optional[str] = None

class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes = True)
    agent_id: str
    agent_name: str
    system_prompt: Optional[str] = None
    sources: list[AgentSource] = Field(default_factory = list)
    indexed_chunk_count: int = 0
    ingestion_status: IngestionStatus
    created_at: Optional[datetime] = None
    faliure_reason: Optional[str] =  None
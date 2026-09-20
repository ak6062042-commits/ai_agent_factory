from enum import Enum

from pydantic import BaseModel, Field, AnyHttpUrl
from typing import Optional


class IngestionStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"

class CreateAgent(BaseModel):
    agent_name: str = Field(..., min_length = 1, description = "Name of the AI agent")
    website_url: AnyHttpUrl = Field(..., min_length = 7, max_length = 2048, description = "Website URL ingested in the agents knowledge base" )

class AgentSource(BaseModel):
    source_type: str
    pdfTitle: str
    page: Optional[int] = None
    websiteTitle: Optional[str] = None
    url: Optional[AnyHttpUrl] = None

class AgentResponse(BaseModel):
    agent_id: str
    agent_name: str
    system_prompt: str
    sources: list[AgentSource] = Field(default_factory = list)
    indexed_chunk_count: int = 0
    ingestion_status: IngestionStatus
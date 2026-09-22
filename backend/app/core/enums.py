from enum import Enum

class IngestionStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"

class SourceType(str, Enum):
    DOCUMENT = "document"
    WEBSITE = "website"

class Roles(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    
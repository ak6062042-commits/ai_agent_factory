from enum import Enum

class IngestionStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"

class SourceType(str, Enum):
    DOCUMENT = "document"
    WEBSITE = "website"
    
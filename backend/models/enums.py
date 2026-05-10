from enum import Enum


class UserRole(str, Enum):
    agent = "agent"
    manager = "manager"
    admin = "admin"


class SessionStatus(str, Enum):
    active = "active"
    resolved = "resolved"
    escalated = "escalated"


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class TicketSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class TicketStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class KnowledgeSourceType(str, Enum):
    web_page = "web_page"
    pdf = "pdf"
    docx = "docx"
    markdown = "markdown"


class KnowledgeSourceStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    indexed = "indexed"
    error = "error"


class MetricType(str, Enum):
    query_count = "query_count"
    resolution_count = "resolution_count"
    escalation_count = "escalation_count"
    avg_confidence = "avg_confidence"
    avg_response_time = "avg_response_time"

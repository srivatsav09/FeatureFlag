from datetime import datetime

from pydantic import BaseModel

from app.models.audit_log import AuditAction


class AuditLogResponse(BaseModel):
    """Schema for audit log in API responses."""

    id: str
    entity_type: str
    entity_id: str
    entity_key: str
    action: AuditAction
    user_id: str
    changes: str | None  # JSON string of changes
    environment_key: str | None
    created_at: datetime

    class Config:
        from_attributes = True

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AuditAction(str, PyEnum):
    """Types of actions that can be audited."""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"


class AuditLog(Base):
    """
    Tracks all changes to flags for accountability and debugging.

    Every create, update, or delete operation creates an audit log entry.
    """

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # What was changed
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "flag", "environment"
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)    # ID of the entity
    entity_key: Mapped[str] = mapped_column(String(100), nullable=False)  # Key for readability

    # What action was taken
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), nullable=False)

    # Who made the change
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False
    )
    user: Mapped["User"] = relationship("User")

    # What changed (stored as JSON string)
    # Example: {"is_enabled": {"old": false, "new": true}}
    changes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # When it happened
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Environment context (if applicable)
    environment_key: Mapped[str | None] = mapped_column(String(50), nullable=True)

    def __repr__(self):
        return f"<AuditLog {self.action.value} {self.entity_type}:{self.entity_key}>"

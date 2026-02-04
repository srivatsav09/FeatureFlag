import uuid
from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Environment(Base):
    """
    Represents a deployment environment (e.g., development, staging, production).
    Each environment can have different flag configurations.
    """

    __tablename__ = "environments"  # Actual table name in PostgreSQL

    # Primary key - using UUID instead of auto-increment integer
    # UUIDs are better for distributed systems and don't expose record count
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # Unique key used in API calls (e.g., "production", "staging")
    key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Human-readable name (e.g., "Production Environment")
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Optional description
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        return f"<Environment {self.key}>"

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, Boolean, Integer, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FlagType(str, PyEnum):
    """Types of feature flags."""
    BOOLEAN = "boolean"      # Simple ON/OFF
    PERCENTAGE = "percentage"  # Gradual rollout (0-100%)


class Flag(Base):
    """
    A feature flag that controls feature availability.
    """

    __tablename__ = "flags"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # Unique key used in code: feature_flags.is_enabled("new-checkout")
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Human-readable name
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # What this flag controls
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Type of flag (boolean or percentage)
    flag_type: Mapped[FlagType] = mapped_column(
        Enum(FlagType),
        default=FlagType.BOOLEAN,
        nullable=False
    )

    # Is this flag enabled? (for boolean flags)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Rollout percentage (for percentage flags, 0-100)
    rollout_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Which environment this flag config belongs to
    environment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("environments.id"),
        nullable=False
    )

    # Relationship - allows flag.environment to get the Environment object
    environment: Mapped["Environment"] = relationship("Environment")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        return f"<Flag {self.key} ({self.environment_id})>"

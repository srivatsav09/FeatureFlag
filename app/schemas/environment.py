from datetime import datetime

from pydantic import BaseModel, Field


class EnvironmentCreate(BaseModel):
    """Schema for creating a new environment."""

    key: str = Field(
        ...,  # Required field
        min_length=1,
        max_length=50,
        pattern=r"^[a-z0-9-]+$",  # Only lowercase, numbers, hyphens
        examples=["production", "staging", "development"]
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        examples=["Production Environment"]
    )
    description: str | None = Field(
        default=None,
        max_length=500
    )


class EnvironmentResponse(BaseModel):
    """Schema for environment in API responses."""

    id: str
    key: str
    name: str
    description: str | None
    created_at: datetime

    class Config:
        # Allow creating this schema from SQLAlchemy model
        from_attributes = True

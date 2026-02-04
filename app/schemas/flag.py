from datetime import datetime

from pydantic import BaseModel, Field

from app.models.flag import FlagType


class FlagCreate(BaseModel):
    """Schema for creating a new flag."""

    key: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9-]+$",  # Only lowercase, numbers, hyphens
        examples=["new-checkout", "dark-mode", "beta-feature"]
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        examples=["New Checkout Flow"]
    )
    description: str | None = Field(
        default=None,
        max_length=1000
    )
    flag_type: FlagType = Field(
        default=FlagType.BOOLEAN,
        examples=[FlagType.BOOLEAN, FlagType.PERCENTAGE]
    )
    is_enabled: bool = Field(default=False)
    rollout_percentage: int = Field(
        default=0,
        ge=0,   # Greater than or equal to 0
        le=100  # Less than or equal to 100
    )
    environment_id: str = Field(
        ...,
        description="The environment this flag belongs to"
    )


class FlagUpdate(BaseModel):
    """Schema for updating an existing flag."""

    name: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    flag_type: FlagType | None = Field(default=None)
    is_enabled: bool | None = Field(default=None)
    rollout_percentage: int | None = Field(default=None, ge=0, le=100)


class FlagResponse(BaseModel):
    """Schema for flag in API responses."""

    id: str
    key: str
    name: str
    description: str | None
    flag_type: FlagType
    is_enabled: bool
    rollout_percentage: int
    environment_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

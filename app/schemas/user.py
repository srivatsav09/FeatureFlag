from datetime import datetime

from pydantic import BaseModel, Field, EmailStr

from app.models.user import UserRole


class UserCreate(BaseModel):
    """Schema for creating a new user (registration)."""

    email: EmailStr = Field(..., examples=["user@example.com"])
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user in API responses (no password!)."""

    id: str
    email: str
    name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for login response with token."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse

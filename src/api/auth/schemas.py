"""Pydantic schemas for authentication."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Schema for user registration."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class Token(BaseModel):
    """Schema for access token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str


class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)."""
    id: int
    username: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class AdminUserCreate(BaseModel):
    """Schema for admin to create a new user."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: Literal["admin", "normal", "viewer"] = "normal"


class AdminUserUpdate(BaseModel):
    """Schema for admin to update a user's role."""
    role: Literal["admin", "normal", "viewer"]


class UserListResponse(BaseModel):
    """Schema for list of users."""
    users: list[UserResponse]
    total: int


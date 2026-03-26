"""User model for authentication."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    """User roles."""
    ADMIN = "admin"
    NORMAL = "normal"
    VIEWER = "viewer"


@dataclass
class User:
    """Represents a user in the system."""
    id: Optional[int]
    username: str
    hashed_password: str
    role: UserRole
    created_at: datetime

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create a User from a dictionary (e.g., from database row)."""
        role_str = data.get("role", "normal")
        role = UserRole(role_str) if isinstance(role_str, str) else UserRole.NORMAL
        
        return cls(
            id=data.get("id"),
            username=data["username"],
            hashed_password=data["hashed_password"],
            role=role,
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at", datetime.now()),
        )

    def to_dict(self) -> dict:
        """Convert User to a dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "hashed_password": self.hashed_password,
            "role": self.role.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    @property
    def is_viewer(self) -> bool:
        return self.role == UserRole.VIEWER

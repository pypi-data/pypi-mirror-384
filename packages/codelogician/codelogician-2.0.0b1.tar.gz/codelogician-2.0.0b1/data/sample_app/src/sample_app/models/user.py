"""User model and management."""

from dataclasses import dataclass
from datetime import datetime

from sample_app.utils.helpers import validate_email


@dataclass
class User:
    """User data model."""

    name: str
    email: str
    created_at: datetime | None = None
    is_active: bool = True

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

        if not validate_email(self.email):
            raise ValueError(f"Invalid email: {self.email}")

    def deactivate(self):
        """Deactivate the user."""
        self.is_active = False

    def activate(self):
        """Activate the user."""
        self.is_active = True


class UserManager:
    """Manages user operations."""

    def __init__(self):
        self.users: list[User] = []

    def add_user(self, user: User) -> None:
        """Add a user to the system."""
        if self.find_user_by_email(user.email):
            raise ValueError(f"User with email {user.email} already exists")
        self.users.append(user)

    def find_user_by_email(self, email: str) -> User | None:
        """Find user by email address."""
        for user in self.users:
            if user.email == email:
                return user
        return None

    def get_active_users(self) -> list[User]:
        """Get all active users."""
        return [user for user in self.users if user.is_active]

    def remove_user(self, email: str) -> bool:
        """Remove user by email."""
        user = self.find_user_by_email(email)
        if user:
            self.users.remove(user)
            return True
        return False

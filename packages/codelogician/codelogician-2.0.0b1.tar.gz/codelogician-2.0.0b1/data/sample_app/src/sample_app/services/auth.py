"""Authentication service."""

import hashlib
import secrets

from ..models.user import User, UserManager


class AuthService:
    """Authentication and authorization service."""

    def __init__(self):
        self.user_manager = UserManager()
        self.sessions = {}

    def hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{pwd_hash}"

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        try:
            salt, pwd_hash = hashed.split(":")
            return hashlib.sha256((password + salt).encode()).hexdigest() == pwd_hash
        except ValueError:
            return False

    def create_session(self, user: User) -> str:
        """Create a session for the user."""
        session_id = secrets.token_urlsafe(32)
        self.sessions[session_id] = user.email
        return session_id

    def get_user_from_session(self, session_id: str) -> User | None:
        """Get user from session ID."""
        email = self.sessions.get(session_id)
        if email:
            return self.user_manager.find_user_by_email(email)
        return None

    def logout(self, session_id: str) -> bool:
        """Logout user by removing session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

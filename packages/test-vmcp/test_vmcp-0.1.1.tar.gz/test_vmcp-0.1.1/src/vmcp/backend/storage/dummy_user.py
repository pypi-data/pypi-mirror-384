"""
Dummy user management for vMCP OSS version.

Creates and manages a single local user to maintain API consistency
while removing authentication complexity.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session
from vmcp.backend.storage.models import User
from vmcp.backend.config import settings

logger = logging.getLogger(__name__)


def get_or_create_dummy_user(db: Session) -> User:
    """
    Get or create the dummy user for local development.

    Args:
        db: Database session

    Returns:
        The dummy user instance
    """
    # Try to get existing dummy user
    user = db.query(User).filter(User.id == 1).first()

    if user is None:
        logger.info("Creating dummy user for local mode...")
        user = User(
            id=1,
            username=settings.dummy_user_id,
            email=settings.dummy_user_email,
            first_name="Local",
            last_name="User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Dummy user created: {user.email}")
    else:
        logger.debug(f"Using existing dummy user: {user.email}")

    return user


def get_dummy_user_context() -> dict:
    """
    Get the dummy user context for dependency injection.

    Returns:
        Dictionary with user_id, user_email, and token
    """
    return {
        "user_id": 1,
        "user_email": settings.dummy_user_email,
        "username": settings.dummy_user_id,
        "token": settings.dummy_user_token,
        "is_dummy": True
    }


class UserContext:
    """
    User context for API dependencies.

    In OSS mode, this always represents the dummy local user.
    """

    def __init__(self, user_id: int = 1, user_email: str = None, username: str = None, token: str = None):
        self.user_id = user_id
        self.user_email = user_email or settings.dummy_user_email
        self.username = username or settings.dummy_user_id
        self.token = token or settings.dummy_user_token
        self.is_dummy = True

    def __repr__(self):
        return f"<UserContext(user_id={self.user_id}, email='{self.user_email}')>"


def ensure_dummy_user():
    """
    Ensure the dummy user exists in the database.

    This is called on startup to initialize the database with the default user.
    """
    from vmcp.backend.storage.database import SessionLocal

    db = SessionLocal()
    try:
        get_or_create_dummy_user(db)
    except Exception as e:
        logger.error(f"Failed to create dummy user: {e}")
        db.rollback()
    finally:
        db.close()


def get_user_context() -> UserContext:
    """
    Dependency for getting user context in FastAPI endpoints.

    Returns:
        UserContext instance for the dummy user
    """
    return UserContext()

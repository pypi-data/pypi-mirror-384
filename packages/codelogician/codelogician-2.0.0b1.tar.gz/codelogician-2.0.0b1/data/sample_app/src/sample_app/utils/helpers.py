"""Helper functions for the application."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def get_config() -> dict[str, Any]:
    """Load application configuration."""
    return {
        "debug": True,
        "database_url": "sqlite:///app.db",
        "secret_key": "dev-key-123",
    }


def process_data(data: dict[str, Any]) -> dict[str, Any]:
    """Process input data and return result."""
    logger.info(f"Processing data: {data}")

    processed = {
        "original": data,
        "processed_at": "2024-01-01T00:00:00Z",
        "status": "success",
    }

    return processed


def validate_email(email: str) -> bool:
    """Simple email validation."""
    return "@" in email and "." in email

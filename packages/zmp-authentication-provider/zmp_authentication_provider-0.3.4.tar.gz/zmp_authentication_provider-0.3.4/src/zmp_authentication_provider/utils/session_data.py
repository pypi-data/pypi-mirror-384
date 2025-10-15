"""InMemorySessionStore is a simple in-memory session store for the authentication provider."""

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SessionData(BaseModel):
    """SessionData is a model for the session data."""

    user_info: dict[str, Any]
    access_token: str
    refresh_token: str
    id_token: str
    expires_at: datetime | None = None

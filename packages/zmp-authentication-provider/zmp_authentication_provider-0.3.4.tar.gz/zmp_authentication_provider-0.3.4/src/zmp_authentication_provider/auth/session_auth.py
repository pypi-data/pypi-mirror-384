"""OAuth2 Keycloak module for the AIops Pilot."""

import logging
from typing import Any

from fastapi import HTTPException, Request, status

from zmp_authentication_provider.setting import auth_default_settings

log = logging.getLogger(__name__)

USER_SESSION_KEY = "user_info"


async def get_session_id_in_cookie(request: Request) -> str:
    """Get the session id from the cookie."""
    session_id: str = request.cookies.get(auth_default_settings.session_id_cookie_name)
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session id is not found in the request session",
        )

    return session_id

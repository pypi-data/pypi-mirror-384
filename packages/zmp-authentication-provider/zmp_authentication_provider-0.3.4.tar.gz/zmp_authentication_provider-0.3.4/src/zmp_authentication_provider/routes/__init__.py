"""Routes module for the authentication provider."""

from fastapi import Request
from fastapi.exceptions import HTTPException

from zmp_authentication_provider.service.auth_service import AuthService
from zmp_authentication_provider.setting import auth_default_settings
from zmp_authentication_provider.utils.redis_session_store import RedisSessionStore


async def get_auth_service(request: Request) -> AuthService:
    """Get the auth service."""
    service = getattr(request.app.state, auth_default_settings.service_name, None)
    if not service:
        raise HTTPException(
            status_code=500,
            detail=f"Service '{auth_default_settings.service_name}' not available in the request state. "
            "You should set the service in the request state.",
        )

    return service


async def get_redis_session_store(request: Request) -> RedisSessionStore:
    """Get the redis session store."""
    redis_session_store = getattr(request.app.state, "redis_session_store", None)
    if not redis_session_store:
        raise HTTPException(
            status_code=500,
            detail="Redis session store not available in the request state. "
            "You should set the redis session store in the request state.",
        )
    return redis_session_store


__all__ = ["get_auth_service", "get_redis_session_store"]

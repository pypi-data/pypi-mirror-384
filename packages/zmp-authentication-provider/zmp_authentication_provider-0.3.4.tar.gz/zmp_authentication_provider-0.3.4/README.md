# ZMP Authentication Provider

A Python library for authentication using Basic Auth and OIDC (OpenID Connect).

## Description

This library provides authentication functionality using both Basic Authentication and OpenID Connect protocols. It's designed to be flexible and easy to integrate into your Python applications.

## Installation

```bash
pip install zmp-authentication-provider
```

## Requirements

- Python >= 3.12, < 4.0

## Dependencies

- pydantic >= 2.10.6
- pydantic-settings >= 2.9.1, < 3.0.0
- fastapi >= 0.115.11, < 0.116.0
- python-dotenv >= 1.0.1, < 2.0.0
- pyjwt >= 2.10.1, < 3.0.0
- requests >= 2.32.3, < 3.0.0
- cryptography >= 42.0.0, < 45.0
- pymongo >= 4.12.0, < 5.0.0
- motor >= 3.7.0, < 4.0.0
- redis >= 5.2.0, < 6.0.0
- uvicorn >= 0.35.0, < 0.36.0
- starlette >= 0.46.2, < 0.47.0
- starlette-csrf >= 3.0.0, < 4.0.0
- colorlog >= 6.9.0, < 7.0.0

## Usage

```python
# FastAPI main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from typing import Callable

from zmp_authentication_provider.routes.auth import router as auth_router
from zmp_authentication_provider.service.auth_service import AuthService
from zmp_authentication_provider.utils.redis_session_store import RedisSessionStore
from zmp_authentication_provider.setting import auth_default_settings, redis_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan for the FastAPI app."""
    try:
        # 1. Initialize MongoDB Connection
        mongodb_client = AsyncIOMotorClient(mongodb_uri)
        database = mongodb_client[database_name]

        # 2. Initialize Redis Session Store
        redis_client = Redis.from_url(
            f"redis://{redis_settings.host}:{redis_settings.port}",
            encoding="utf-8",
            decode_responses=redis_settings.decode_responses,
            db=redis_settings.db,
            password=redis_settings.password,
        )
        app.state.redis_session_store = RedisSessionStore(
            redis_client=redis_client,
            session_ttl=auth_default_settings.session_ttl
        )

        # 3. Initialize Auth Service
        app.state.auth_service = await AuthService.initialize(database=database)

        yield

    finally:
        if mongodb_client:
            await mongodb_client.close()
        if redis_client:
            await redis_client.close()

app = FastAPI(
    title="Your Application",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth_router, tags=["auth"], prefix="/api/v1")


# router.py
from zmp_authentication_provider.auth.oauth2_keycloak import (
    TokenData,
    get_current_user,
)


@router.put(
    "/jobs/{job_id}",
    summary="Update job details",
    description="Update the details of an existing job. Only the provided fields will be updated.",
    response_description="The updated job information.",
    response_class=JSONResponse,
    response_model=Job,
    response_model_by_alias=False,
    response_model_exclude_none=False,
)
async def update_job(
    job_update_request: JobUpdateRequest,
    job_id: str = Path(..., description="The ID of the job to update"),
    service: AIOpsService = Depends(_get_aiops_service),
    oauth_user: TokenData = Depends(get_current_user),
):
    """Update a job's information."""
    job = Job(
        id=job_id,
        updated_by=oauth_user.username,
        **job_update_request.model_dump(exclude_unset=True),
    )
    return await service.modify_job(job=job)

```

### Sliding Session Management

To implement sliding session expiration (automatic session extension on user activity), add the following middleware to your FastAPI application:

```python
from typing import Callable
from fastapi import Request, Response
from zmp_authentication_provider.setting import auth_default_settings
from zmp_authentication_provider.utils.redis_session_store import RedisSessionStore

@app.middleware("http")
async def sliding_session_middleware(
    request: Request, call_next: Callable[[Request], Response]
):
    """Sliding session middleware.

    This middleware extends session TTL on every request (sliding expiration).
    It updates both Redis TTL and cookie max-age to keep them synchronized.
    """
    resp: Response = await call_next(request)

    # Apply sliding expiration for existing sessions
    session_id = request.cookies.get(auth_default_settings.session_id_cookie_name)
    session_id_created = getattr(request.state, "session_id_created", False)
    if session_id and not session_id_created:
        redis_session_store: RedisSessionStore = request.app.state.redis_session_store
        # Extend both Redis TTL and cookie max-age (sliding expiration)
        await redis_session_store.reset_ttl(session_id)
        resp.set_cookie(
            key=auth_default_settings.session_id_cookie_name,
            value=session_id,
            max_age=auth_default_settings.session_max_age,
            httponly=auth_default_settings.session_https_only,
            secure=auth_default_settings.session_secure,
            samesite=auth_default_settings.session_same_site,
            domain=auth_default_settings.session_domain,
        )

    return resp
```

This middleware automatically extends the session expiration time on every request, ensuring users remain logged in while actively using the application.

### Environment Configuration

Put the below value into the`.env` file in your project root:

```env
# Authentication default configuration
AUTH_HTTP_CLIENT_SSL_VERIFY="True"
AUTH_APPLICATION_ENDPOINT="${YOUR_API_ENDPOINT}"
AUTH_SESSION_TTL="1800"
AUTH_SESSION_MAX_AGE="1800"
AUTH_SESSION_DOMAIN="your-domain.com"
AUTH_SESSION_SECURE="True"
AUTH_SESSION_HTTPS_ONLY="True"
AUTH_SESSION_SAME_SITE="lax"

# Keycloak configuration
KEYCLOAK_SERVER_URL="https://your-keycloak-server.com/auth"
KEYCLOAK_REALM="your-realm"
KEYCLOAK_CLIENT_ID="your-client-id"
KEYCLOAK_CLIENT_SECRET="your-client-secret"
KEYCLOAK_REDIRECT_URI="${AUTH_APPLICATION_ENDPOINT}/api/v1/auth/oauth2/callback"
KEYCLOAK_ALGORITHM="RS256"

# Redis configuration
REDIS_HOST="localhost"
REDIS_PORT="6379"
REDIS_DB="0"
REDIS_PASSWORD=""
REDIS_DECODE_RESPONSES="True"
REDIS_SESSION_PREFIX="session:"
REDIS_SESSION_TTL="1800"
```

## Development

### Development Dependencies

```bash
pip install pytest pytest-cov pytest-watcher pytest-asyncio certifi ruff
```

### Quality Tools

```bash
pip install pre-commit
```

## Project Structure

The main package is located in the `src/zmp_authentication_provider` directory.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the terms of the license included in the repository.

## Author

- Kilsoo Kang (kilsoo75@gmail.com)

## Links

- [Homepage](https://github.com/cloudz-mp)
- [Repository](https://github.com/cloudz-mp/zmp-authentication-provider)
- [Documentation](https://github.com/cloudz-mp/zmp-authentication-provider)
- [Issue Tracker](https://github.com/cloudz-mp/zmp-authentication-provider/issues)

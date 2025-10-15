"""Auth routes."""

import base64
import json
import logging
import secrets

import requests
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from zmp_authentication_provider.auth.oauth2_keycloak import (
    KEYCLOAK_AUTH_ENDPOINT,
    KEYCLOAK_CLIENT_ID,
    KEYCLOAK_CLIENT_SECRET,
    KEYCLOAK_END_SESSION_ENDPOINT,
    KEYCLOAK_REDIRECT_URI,
    KEYCLOAK_SCOPE,
    KEYCLOAK_TOKEN_ENDPOINT,
    KEYCLOAK_USER_ENDPOINT,
    TokenData,
    get_current_user,
    verify_token,
)
from zmp_authentication_provider.auth.session_auth import (
    get_session_id_in_cookie,
)
from zmp_authentication_provider.exceptions import (
    AuthBackendException,
    AuthError,
)
from zmp_authentication_provider.routes import get_auth_service, get_redis_session_store
from zmp_authentication_provider.scheme.auth_model import OAuthUser
from zmp_authentication_provider.service.auth_service import AuthService
from zmp_authentication_provider.setting import auth_default_settings
from zmp_authentication_provider.utils.redis_session_store import (
    RedisSessionStore,
)
from zmp_authentication_provider.utils.session_data import (
    SessionData,
)

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.get("/home", summary="Home page", response_class=HTMLResponse)
async def home(
    request: Request,
    redis_session_store: RedisSessionStore = Depends(get_redis_session_store),
):
    """Get home page."""
    # check the session_id in the cookie
    csrf_token = request.cookies.get(auth_default_settings.csrf_token_cookie_name)
    session_id = request.cookies.get(auth_default_settings.session_id_cookie_name)

    logger.debug(f"csrf_token: {csrf_token}")
    logger.debug(f"session_id: {session_id}")

    if csrf_token and session_id:
        session_data = await redis_session_store.get(session_id)
        if not session_data:
            raise AuthBackendException(
                AuthError.OAUTH_IDP_ERROR,
                details="Session data is not found in the redis session store",
            )

        user_info = session_data.user_info
        if not user_info:
            await redis_session_store.delete(session_id)
            return HTMLResponse(
                content="Session data has been lost "
                "because the server has been restared."
                "Please login again",
            )
        else:
            return HTMLResponse(content=f"<p>User info</p><p>{user_info}</p>")
    else:
        return HTMLResponse(content="<p>No user info. Please login again.</p>")


@router.get(
    "/authenticate",
    summary="Process the authentication",
    response_class=RedirectResponse,
)
async def authenticate(
    request: Request,
    redis_session_store: RedisSessionStore = Depends(get_redis_session_store),
):
    """Authenticate whether the user is logged in or not."""
    # check the session_id in the cookie
    csrf_token = request.cookies.get(auth_default_settings.csrf_token_cookie_name)
    session_id = request.cookies.get(auth_default_settings.session_id_cookie_name)

    logger.debug(f"csrf_token: {csrf_token}")
    logger.debug(f"session_id: {session_id}")

    # for the redirect to the referer
    referer = request.headers.get("referer")
    # referer = referer or "/"
    if not referer:
        # raise AuthBackendException(
        #     AuthError.OAUTH_IDP_ERROR,
        #     details="Referer is not found in the request header",
        # )
        referer = f"{auth_default_settings.application_endpoint_for_referer}"

    logger.debug(f"referer: {referer}")

    if csrf_token and session_id:
        # NOTE: in the session middleware, the session data is stored in the request state, not in the cookie
        # NOTE: the session data is stored in the redis session store
        # access_token = request.state.session_data.access_token
        session_data = await redis_session_store.get(session_id)

        if session_data is None:
            # request.state.session_data = None
            # await redis_session_store.delete(session_id)
            logger.error(
                "Session data is not found in the redis session store. Please login again",
            )
            return RedirectResponse(
                url=f"{KEYCLOAK_AUTH_ENDPOINT}?response_type=code"
                f"&client_id={KEYCLOAK_CLIENT_ID}"
                f"&state={csrf_token}{auth_default_settings.state_separator}{referer}"
                f"&redirect_uri={KEYCLOAK_REDIRECT_URI}"
                f"&scope={KEYCLOAK_SCOPE}"
            )
        else:
            logger.debug(f"access_token: {session_data.access_token[:100]}...")

            return RedirectResponse(url=f"{referer}")
    else:
        return RedirectResponse(
            url=f"{KEYCLOAK_AUTH_ENDPOINT}?response_type=code"
            f"&client_id={KEYCLOAK_CLIENT_ID}"
            f"&state={csrf_token}{auth_default_settings.state_separator}{referer}"
            f"&redirect_uri={KEYCLOAK_REDIRECT_URI}"
            f"&scope={KEYCLOAK_SCOPE}"
        )


@router.get(
    "/logout",
    summary="Logout from the keyclaok",
    response_class=RedirectResponse,
)
async def logout(
    request: Request,
    redis_session_store: RedisSessionStore = Depends(get_redis_session_store),
):
    """Logout."""
    csrf_token = request.cookies.get(auth_default_settings.csrf_token_cookie_name)
    session_id = request.cookies.get(auth_default_settings.session_id_cookie_name)
    if not csrf_token or not session_id:
        # raise AuthBackendException(
        #     AuthError.SESSION_EXPIRED,
        #     details="No csrf token in cookie and session id in cookie",
        # )
        logger.error(
            "No csrf token in cookie and session id in cookie",
        )
        return RedirectResponse(
            url=f"{auth_default_settings.application_endpoint}/auth/authenticate",
            headers={
                "referer": f"{auth_default_settings.application_endpoint_for_referer}"
            },
        )
    else:
        session_data = await redis_session_store.get(session_id)
        if not session_data:
            raise AuthBackendException(
                AuthError.OAUTH_IDP_ERROR,
                details="Session data is not found in the redis session store",
            )

        refresh_token = session_data.refresh_token
        if not refresh_token:
            raise AuthBackendException(
                AuthError.OAUTH_IDP_ERROR,
                details="Refresh token is not found in the session data",
            )
        else:
            # 1. logout from the keycloak
            data = {
                "client_id": KEYCLOAK_CLIENT_ID,
                "client_secret": KEYCLOAK_CLIENT_SECRET,
                "refresh_token": refresh_token,
            }
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            idp_response = requests.post(
                KEYCLOAK_END_SESSION_ENDPOINT,
                data=data,
                headers=headers,
                verify=auth_default_settings.http_client_ssl_verify,
            )

            if idp_response.status_code != 204:
                raise AuthBackendException(
                    AuthError.OAUTH_IDP_ERROR,
                    details=f"Failed to logout.({idp_response.reason})",
                )

        # 2. delete the session data from the redis session store
        await redis_session_store.delete(session_id)

        # 3. clear the session_data in the request state
        request.state.session_data = None

        # NOTE: go to the authenticate endpoint with the referer (/) after logout
        redirect_response = RedirectResponse(
            url=f"{auth_default_settings.application_endpoint}/auth/authenticate",
            headers={
                "referer": f"{auth_default_settings.application_endpoint_for_referer}"
            },
        )

        # 4. clear the session id cookie
        # NOTE: the csrf token cookie should be kept for the next request
        redirect_response.delete_cookie(
            key=auth_default_settings.session_id_cookie_name,
            domain=auth_default_settings.session_domain,
            secure=auth_default_settings.session_secure,
            httponly=auth_default_settings.session_https_only,
            samesite=auth_default_settings.session_same_site,
        )

        return redirect_response


@router.get("/oauth2/callback", summary="Keycloak OAuth2 callback for the redirect URI")
async def callback(
    request: Request,
    code: str,
    state: str,
    auth_service: AuthService = Depends(get_auth_service),
    redis_session_store: RedisSessionStore = Depends(get_redis_session_store),
):
    """Keycloak OAuth2 callback for the redirect URI."""
    csrf_token = request.cookies.get(auth_default_settings.csrf_token_cookie_name)

    state = state.split(auth_default_settings.state_separator)
    received_csrf_token = state[0]
    referer = state[1]

    logger.debug(f"cookie csrftoken: {csrf_token}")
    logger.debug(f"state: {state}")
    logger.debug(f"received csrftoken: {received_csrf_token}")
    logger.debug(f"referer: {referer}")

    # check the csrf token
    if received_csrf_token != csrf_token:
        raise AuthBackendException(
            AuthError.OAUTH_IDP_ERROR,
            details=f"CSRF token mismatch.({received_csrf_token} != {csrf_token})",
        )

    # get the tokens from the keycloak
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": KEYCLOAK_REDIRECT_URI,
        "client_id": KEYCLOAK_CLIENT_ID,
        "client_secret": KEYCLOAK_CLIENT_SECRET,
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    idp_response = requests.post(
        KEYCLOAK_TOKEN_ENDPOINT,
        data=data,
        headers=headers,
        verify=auth_default_settings.http_client_ssl_verify,
    )

    if idp_response.status_code != 200:
        raise AuthBackendException(
            AuthError.OAUTH_IDP_ERROR,
            details=f"Failed to obtain token.({idp_response.reason})",
        )

    tokens = idp_response.json()

    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    id_token = tokens.get("id_token")

    # get the user info from the keycloak for the OAuthUser creation and session data
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    idp_response = requests.get(
        KEYCLOAK_USER_ENDPOINT,
        headers=headers,
        verify=auth_default_settings.http_client_ssl_verify,
    )
    if idp_response.status_code != 200:
        raise AuthBackendException(
            AuthError.OAUTH_IDP_ERROR,
            details=f"Failed to fetch user info.({idp_response.reason})",
        )

    user_info = idp_response.json()
    logger.debug(f"user_info: {user_info}")

    # create the oauth user if the enable_oauth_user_creation is True
    if auth_default_settings.enable_oauth_user_creation:
        # NOTE: the userinfo does not have the iss, so we need to verify the id_token for OAuthUser creation
        token_data = verify_token(id_token)
        oauth_user = OAuthUser(
            iss=token_data.iss,
            sub=token_data.sub,
            username=token_data.username,
            email=token_data.email,
            given_name=token_data.given_name,
            family_name=token_data.family_name,
        )

        logger.debug(f"oauth_user: {oauth_user}")

        await auth_service.upsert_oauth_user(oauth_user)

    # check the session id exists or not, if exists, use the session id, otherwise generate a random token for the session id
    session_id = request.cookies.get(auth_default_settings.session_id_cookie_name)
    if not session_id:
        new_session_id = secrets.token_urlsafe(32)
        # set the state for the session id created
        request.state.session_id_created = True
    else:
        new_session_id = session_id
        # set the state for the session id created
        request.state.session_id_created = False

    # create the session data
    session_data = SessionData(
        user_info=user_info,
        access_token=access_token,
        refresh_token=refresh_token,
        id_token=id_token,
    )

    # store the session data in the redis session store
    await redis_session_store.set(new_session_id, session_data)

    # If the same-site of cookie is 'lax', the cookie will be sent only if the request is same-site request
    # If the same-site of cookie is 'strict', the cookie will not be sent
    resposne = RedirectResponse(
        # url=f"{auth_default_settings.application_endpoint}/auth/home"
        url=f"{referer}"
    )

    # set the cookie for the session id
    if request.state.session_id_created:
        resposne.set_cookie(
            key=auth_default_settings.session_id_cookie_name,
            value=new_session_id,
            domain=auth_default_settings.session_domain,
            httponly=auth_default_settings.session_https_only,
            max_age=auth_default_settings.session_max_age,
            samesite=auth_default_settings.session_same_site,
            secure=auth_default_settings.session_secure,
        )

    return resposne


@router.get(
    "/access-token", summary="Get the access token from the redis session store"
)
@router.get(
    "/access_token",
    summary="Get the access token from the redis session store",
    deprecated=True,
)
async def get_access_token(
    session_id: str = Depends(get_session_id_in_cookie),
    redis_session_store: RedisSessionStore = Depends(get_redis_session_store),
):
    """Get the access token from the redis session store."""
    session_data = await redis_session_store.get(session_id)
    if not session_data:
        raise AuthBackendException(
            AuthError.OAUTH_IDP_ERROR,
            details="Session data is not found in the redis session store",
        )

    # NOTE: sliding expiration should be handled in the session middleware on application side
    # await redis_session_store.reset_ttl(session_id)

    return {"access_token": session_data.access_token}


@router.patch(
    "/refresh-token", summary="Refresh the access token using the refresh token"
)
@router.patch(
    "/refresh_token",
    summary="Refresh the access token using the refresh token",
    deprecated=True,
)
async def refresh_access_token(
    session_id: str = Depends(get_session_id_in_cookie),
    redis_session_store: RedisSessionStore = Depends(get_redis_session_store),
):
    """Refresh the access token using the refresh token."""
    session_data = await redis_session_store.get(session_id)
    if not session_data:
        raise AuthBackendException(
            AuthError.OAUTH_IDP_ERROR,
            details="Session data is not found in the redis session store",
        )

    refresh_token = session_data.refresh_token
    if not refresh_token:
        raise AuthBackendException(
            AuthError.OAUTH_IDP_ERROR,
            details="Refresh token is not found in the session data",
        )

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": KEYCLOAK_CLIENT_ID,
        "client_secret": KEYCLOAK_CLIENT_SECRET,
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    idp_response = requests.post(
        KEYCLOAK_TOKEN_ENDPOINT,
        data=data,
        headers=headers,
        verify=auth_default_settings.http_client_ssl_verify,
    )

    if idp_response.status_code != 200:
        raise AuthBackendException(
            AuthError.OAUTH_IDP_ERROR,
            details=f"Failed to refresh the access token.({idp_response.reason})",
        )

    refreshed_tokens = idp_response.json()
    # TODO: check the tokens whether the access token, refresh token, and id token are included in the tokens
    logger.debug(f"tokens: {refreshed_tokens}")

    if not refreshed_tokens.get("access_token"):
        raise AuthBackendException(
            AuthError.OAUTH_IDP_ERROR,
            details="Access token is not found in the response",
        )
    else:
        # update the session data in the redis session store with the new tokens
        session_data = SessionData(
            user_info=session_data.user_info,
            access_token=refreshed_tokens.get("access_token"),
            refresh_token=refreshed_tokens.get("refresh_token"),
            id_token=refreshed_tokens.get("id_token"),
        )

        await redis_session_store.set(session_id, session_data)

        return {"access_token": session_data.access_token}


@router.get("/profile", summary="Get the current user profile from Token")
async def profile(
    request: Request,
    oauth_user: TokenData = Depends(get_current_user),
    redis_session_store: RedisSessionStore = Depends(get_redis_session_store),
):
    """Get the current user profile from Token."""
    session_id = request.cookies.get(auth_default_settings.session_id_cookie_name)
    session_data = await redis_session_store.get(session_id)
    if not session_data:
        raise AuthBackendException(
            AuthError.SESSION_EXPIRED,
            details="Session data is not found in the redis session store",
        )

    # NOTE: sliding expiration should be handled in the session middleware on application side
    # await redis_session_store.reset_ttl(session_id)

    return oauth_user


async def _check_session_data_size(session_data: SessionData):
    """Check the session data size."""
    json_session = json.dumps(session_data)
    logger.debug(f"json_session: {json_session}")
    logger.debug(f"json_session bytes: {len(json_session.encode('utf-8'))}")

    base64_encoded_session = base64.b64encode(json_session.encode("utf-8"))
    logger.debug(f"base64_encoded_session: {base64_encoded_session}")

    total_bytes = len(base64_encoded_session)
    logger.debug(f"base64_encoded_session bytes: {total_bytes}")

    if total_bytes > (4 * 1024):
        logger.debug(f"Total bytes: {total_bytes}")
        logger.warning(f"The session data size({total_bytes}) is over than 4kb.")
        raise AuthBackendException(
            AuthError.TOKEN_DATA_TOO_LARGE,
            details=f"The session data size is {total_bytes} bytes. It is over than 4kb.",
        )

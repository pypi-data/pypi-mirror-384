"""RedisSessionStore for distributed session management using Redis."""

import json
import logging
from datetime import datetime, timedelta

from redis.asyncio import Redis

from zmp_authentication_provider.setting import redis_settings
from zmp_authentication_provider.utils.session_data import SessionData
from zmp_authentication_provider.utils.time_utils import DEFAULT_TIME_ZONE

logger = logging.getLogger(__name__)


class RedisSessionStore:
    """RedisSessionStore for distributed session management using Redis."""

    def __init__(self, redis_client: Redis, session_ttl: int | None = None):
        """Initialize the RedisSessionStore with a Redis client.

        Args:
            redis_client: Redis client instance for session storage
            session_ttl: Session TTL in seconds (uses redis_settings.session_ttl if not provided)
        """
        self.redis_client = redis_client
        self.session_ttl = session_ttl or redis_settings.session_ttl
        self.session_prefix = redis_settings.session_prefix
        logger.info(
            f"RedisSessionStore initialized with TTL: {self.session_ttl}s, "
            f"prefix: {self.session_prefix}"
        )

    def _get_key(self, unique_id: str) -> str:
        """Generate Redis key with prefix.

        Args:
            unique_id: Unique identifier for the session

        Returns:
            Redis key with prefix
        """
        return f"{self.session_prefix}{unique_id}"

    async def get(self, unique_id: str) -> SessionData | None:
        """Get session data from Redis.

        Args:
            unique_id: Unique identifier for the session

        Returns:
            SessionData if found, None otherwise
        """
        try:
            key = self._get_key(unique_id)
            data = await self.redis_client.get(key)
            if data:
                session_dict = json.loads(data)
                # Convert ISO format string back to datetime
                if session_dict.get("expires_at"):
                    session_dict["expires_at"] = datetime.fromisoformat(
                        session_dict["expires_at"]
                    )
                return SessionData(**session_dict)
            return None
        except Exception as e:
            logger.error(f"Failed to get session for {unique_id}: {e}")
            return None

    async def set(self, unique_id: str, session_data: SessionData):
        """Set session data in Redis with TTL.

        Args:
            unique_id: Unique identifier for the session
            session_data: SessionData instance to store
        """
        try:
            key = self._get_key(unique_id)

            # Set expires_at timestamp
            session_data.expires_at = datetime.now(DEFAULT_TIME_ZONE) + timedelta(
                seconds=self.session_ttl
            )

            # Convert SessionData to dict and handle datetime serialization
            session_dict = session_data.model_dump()
            if session_dict.get("expires_at"):
                if isinstance(session_dict["expires_at"], datetime):
                    session_dict["expires_at"] = session_dict["expires_at"].isoformat()
                else:
                    session_dict["expires_at"] = session_dict["expires_at"]

            # Store in Redis with TTL
            await self.redis_client.setex(
                key, self.session_ttl, json.dumps(session_dict, ensure_ascii=False)
            )
            logger.debug(
                f"Session for {unique_id} stored with TTL {self.session_ttl}s, "
                f"expires at {session_data.expires_at}"
            )
        except Exception as e:
            logger.error(f"Failed to set session for {unique_id}: {e}")
            raise

    async def reset_ttl(self, unique_id: str):
        """Reset the TTL for an existing session.

        Args:
            unique_id: Unique identifier for the session
        """
        try:
            session_data = await self.get(unique_id)
            if session_data:
                # Re-store with new TTL
                await self.set(unique_id, session_data)
                logger.info(
                    f"Session TTL for {unique_id} reset until {session_data.expires_at}"
                )
            else:
                logger.warning(f"Cannot reset TTL: session {unique_id} not found")
        except Exception as e:
            logger.error(f"Failed to reset TTL for {unique_id}: {e}")
            raise

    async def delete(self, unique_id: str):
        """Delete session data from Redis.

        Args:
            unique_id: Unique identifier for the session
        """
        try:
            key = self._get_key(unique_id)
            result = await self.redis_client.delete(key)
            if result:
                logger.info(f"Session for {unique_id} deleted")
            else:
                logger.debug(f"Session for {unique_id} not found (already deleted)")
        except Exception as e:
            logger.error(f"Failed to delete session for {unique_id}: {e}")
            raise

    async def close(self):
        """Close Redis connection gracefully."""
        try:
            await self.redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")

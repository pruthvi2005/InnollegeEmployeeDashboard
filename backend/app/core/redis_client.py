import time
import logging
from typing import Optional, Dict
import redis
from app.config import settings

logger = logging.getLogger(__name__)

# Fallback in-memory store for test/dev environments without active Redis
_in_memory_store: Dict[str, tuple[str, float]] = {}


class RedisManager:
    """Manages Redis connection with in-memory fallback for resilience."""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None
        self._connected: bool = False
        self._init_client()

    def _init_client(self) -> None:
        try:
            self._client = redis.Redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=2.0,
                socket_connect_timeout=2.0,
            )
            # Ping test
            self._client.ping()
            self._connected = True
            logger.info("Connected to Redis successfully.")
        except Exception as e:
            self._connected = False
            logger.warning("Redis connection unavailable (%s). Using in-memory fallback.", e)

    @property
    def client(self) -> Optional[redis.Redis]:
        if not self._connected:
            try:
                if self._client:
                    self._client.ping()
                    self._connected = True
            except Exception:
                self._connected = False
        return self._client if self._connected else None


_redis_manager = RedisManager(settings.REDIS_URL)


def get_redis() -> Optional[redis.Redis]:
    """Retrieve Redis client instance."""
    return _redis_manager.client


def set_with_ttl(key: str, value: str, ttl_seconds: int) -> bool:
    """Store key-value pair with TTL in seconds."""
    r = get_redis()
    if r:
        try:
            r.setex(key, ttl_seconds, value)
            return True
        except Exception as e:
            logger.error("Redis setex error: %s", e)
    # In-memory fallback
    expire_at = time.time() + ttl_seconds
    _in_memory_store[key] = (value, expire_at)
    return True


def get_value(key: str) -> Optional[str]:
    """Retrieve value by key, checking expiration."""
    r = get_redis()
    if r:
        try:
            return r.get(key)
        except Exception as e:
            logger.error("Redis get error: %s", e)
    # In-memory fallback
    if key in _in_memory_store:
        val, expire_at = _in_memory_store[key]
        if time.time() < expire_at:
            return val
        else:
            del _in_memory_store[key]
    return None


def delete_key(key: str) -> bool:
    """Delete a key from storage."""
    r = get_redis()
    if r:
        try:
            return bool(r.delete(key))
        except Exception as e:
            logger.error("Redis delete error: %s", e)
    if key in _in_memory_store:
        del _in_memory_store[key]
        return True
    return False


def blacklist_token(jti: str, ttl_seconds: int) -> bool:
    """Blacklist a JWT JTI ID until token expiration."""
    key = f"bl:{jti}"
    return set_with_ttl(key, "revoked", ttl_seconds)


def is_blacklisted(jti: str) -> bool:
    """Check if token JTI has been revoked/blacklisted."""
    key = f"bl:{jti}"
    return get_value(key) is not None

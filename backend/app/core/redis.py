import redis.asyncio as redis
from app.core.config import settings

_redis_client = None

async def get_redis():
    """Return Redis client, or None if unavailable."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            # Test connection
            await _redis_client.ping()
        except Exception:
            _redis_client = None
    return _redis_client

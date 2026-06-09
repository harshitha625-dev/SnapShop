import json, redis
import logging
from backend.config import settings

_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)
CACHE_TTL = 6 * 60 * 60   # 6 hours in seconds
logger = logging.getLogger(__name__)

# ── Local fallback for Windows/Dev ──
_local_cache = {}
_redis_available = True

def get_cached(image_hash: str) -> dict | None:
    """Cache key = 'search:{sha256_hash}'. Falls back to memory if Redis is down."""
    global _redis_available
    
    # Try Redis first
    if _redis_available:
        try:
            raw = redis.Redis(connection_pool=_pool).get(f"search:{image_hash}")
            if raw:
                return json.loads(raw)
        except redis.exceptions.ConnectionError:
            logger.warning("Redis not found. Falling back to in-memory cache.")
            _redis_available = False  # Switch to local for this session
        except Exception as e:
            logger.error(f"Redis get error: {e}")

    # Fallback to local memory
    return _local_cache.get(image_hash)

def set_cache(image_hash: str, data: dict) -> None:
    """Store search result with TTL. Falls back to memory if Redis is down."""
    global _redis_available
    
    if _redis_available:
        try:
            redis.Redis(connection_pool=_pool).setex(
                name=f"search:{image_hash}",
                time=CACHE_TTL,
                value=json.dumps(data),
            )
            return
        except redis.exceptions.ConnectionError:
            _redis_available = False
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    # Fallback: store in local dict
    _local_cache[image_hash] = data
import json
import redis

from app.config import settings


# Create Redis connection
# decode_responses=True means we get strings back, not bytes
redis_client = redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


class CacheService:
    """
    Service for caching flag configurations in Redis.
    """

    def __init__(self):
        self.client = redis_client
        self.ttl = settings.cache_ttl_seconds

    def _make_key(self, flag_key: str, environment_key: str) -> str:
        """
        Create a cache key for a flag.

        Format: flag:{environment}:{flag_key}
        Example: flag:production:new-checkout
        """
        return f"flag:{environment_key}:{flag_key}"

    def get_flag(self, flag_key: str, environment_key: str) -> dict | None:
        """
        Get a flag config from cache.

        Returns:
            Flag config dict if found, None if not cached
        """
        key = self._make_key(flag_key, environment_key)
        data = self.client.get(key)

        if data:
            return json.loads(data)
        return None

    def set_flag(self, flag_key: str, environment_key: str, flag_data: dict) -> None:
        """
        Cache a flag config.

        Args:
            flag_key: The flag key
            environment_key: The environment key
            flag_data: The flag configuration to cache
        """
        key = self._make_key(flag_key, environment_key)
        self.client.setex(
            key,
            self.ttl,  # Expires after TTL seconds
            json.dumps(flag_data),
        )

    def invalidate_flag(self, flag_key: str, environment_key: str) -> None:
        """
        Remove a flag from cache (called when flag is updated).
        """
        key = self._make_key(flag_key, environment_key)
        self.client.delete(key)

    def invalidate_environment(self, environment_key: str) -> None:
        """
        Remove all flags for an environment from cache.
        Uses pattern matching to find and delete all related keys.
        """
        pattern = f"flag:{environment_key}:*"
        keys = self.client.keys(pattern)
        if keys:
            self.client.delete(*keys)

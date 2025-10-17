import json
import logging
import time

import redis
from django.conf import settings

logger = logging.getLogger('normal')


class RedisDataLayer:

    def __init__(self, redis_url=settings.IOS_REDIS_CACHE, max_retries=3):
        """Initialize RedisDataLayer with a Redis client connection.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.client = self.__connect_redis_client(max_retries=max_retries)

    def __connect_redis_client(self, max_retries=3, retry_delay=1.0):
        """
        Returns a Redis client instance configured with settings and retry mechanism.

        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries in seconds

        Returns:
            Redis client instance or None if all retries failed
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                # Create Redis client (no ping test)
                client = redis.StrictRedis.from_url(self.redis_url)

                if attempt > 0:
                    logger.info(
                        f"Redis client creation successful on attempt {attempt + 1}"
                    )

                return client

            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Redis client creation attempt {attempt + 1} failed: {str(e)}"
                )

            # Don't sleep after the last attempt
            if attempt < max_retries:
                logger.info(
                    f"Retrying Redis client creation in {retry_delay:.1f} seconds..."
                )
                time.sleep(retry_delay)

        # All retries failed
        logger.exception(
            "Error while setting connection with redis", str(last_exception)
        )
        return None

    def store_data_in_redis_cache(
        self,
        key,
        value,
        ttl=int(settings.REFRESH_TOKEN_EXPIRY_DAYS) * 86400,
        user_id=None,
    ):
        try:
            redis_client = self.client
            redis_client.setex(name=key, time=ttl, value=value)

            if user_id:
                user_keys_set = f"user_keys:{user_id}"
                # Store key mapping in a set for this user
                redis_client.sadd(user_keys_set, key)
                # Ensure the set expires after ttl
                redis_client.expire(user_keys_set, ttl)

            return True

        except redis.exceptions.ConnectionError as e:
            logger.exception("Redis connection error", str(e))
            return False

        except Exception as e:
            logger.exception("Error while setting cache", str(e))
            return False

    def get_data_from_redis_cache(self, key):
        """
        Retrieve data from Redis cache using the provided key.

        Args:
            key: The cache key to retrieve data for

        Returns:
            dict: The cached data or None if not found
            dict: {'connection_error': True} if connection fails
        """
        try:
            cached_data = self.client.get(key)
            if not cached_data:
                return None

            data = json.loads(cached_data)
            return data

        except redis.exceptions.ConnectionError as e:
            logger.exception("Redis connection error", str(e))
            return {"connection_error": True}

        except Exception as e:
            logger.exception("Error while getting data from cache", str(e))
            return None

    def delete_data_from_redis_cache(self, key, user_id=None):
        """
        Delete data from Redis cache using the provided key.
        Optionally deletes all user-associated keys if user_id is provided.

        Args:
            key: The cache key to delete
            user_id: Optional user ID to delete all associated keys

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if isinstance(key, list):
                self.client.delete(*key)
            else:
                self.client.delete(key)

            if user_id:
                user_keys_set = f"user_keys:{user_id}"
                user_keys = self.client.smembers(user_keys_set)

                if user_keys:
                    # Add member keys and add the individual key
                    keys_to_delete = {key.decode("utf-8") for key in user_keys}

                    # delete member keys
                    self.client.delete(*keys_to_delete)

                    # Delete the set itself
                    self.client.delete(user_keys_set)

            return True

        except redis.exceptions.ConnectionError as e:
            logger.exception("Redis connection error", str(e))
            return False

        except Exception as e:
            logger.exception("Error while deleting cache", str(e))
            return False

    def check_and_set_cache(self, cache_key, ttl=60):
        """
        Checks if a similar request exists in the cache based on cache key.
        If not, adds the cache key with TTL of 1 minute.

        Args:
            cache_key: The cache key to check and set
            ttl: Time to live in seconds (default: 60 seconds)

        Returns:
            bool: True if key was set (didn't exist), False if key already exists
        """
        try:
            if self.client.exists(cache_key):
                return False

            self.client.setex(name=cache_key, time=ttl, value="PENDING")
            return True

        except Exception as e:
            logger.exception("Error while setting cache", str(e))
            return False

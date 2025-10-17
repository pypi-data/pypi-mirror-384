from typing import List, Dict, Any

import redis
from fastapi import HTTPException

from .schema import RedisKey, RedisInfo, SlowLogEntry

import pickle

def try_unpickle(value_data):
    """
    Try to detect and decode pickled data safely.
    Returns:
        - Tuple (is_pickled: bool, value: Any)
    """
    if not value_data:
        return False, value_data

    # Make sure it's bytes
    if isinstance(value_data, str):
        try:
            value_data = value_data.encode('utf-8')
        except Exception:
            return False, value_data

    try:
        # Try to unpickle
        value = pickle.loads(value_data)
        return True, value
    except (pickle.UnpicklingError, EOFError, AttributeError, ValueError, TypeError):
        return False, value_data

class RedisConnection:
    def __init__(self, db: int = None):
        # Get settings from config
        from .config import RedisToolsSettings
        self.settings = RedisToolsSettings()

        # Use provided db or default from settings
        db_to_use = db if db is not None else self.settings.redis_db

        # Create Redis client with settings
        self.client = self._create_client(db_to_use)

    def _create_client(self, db: int = 0) -> redis.Redis:
        if self.settings.REDIS_DSN:
            return redis.from_url(
                self.settings.REDIS_DSN,
                db=db,
                decode_responses=self.settings.redis_decode_responses
            )
        return redis.Redis(
            host=self.settings.redis_host,
            port=self.settings.redis_port,
            ssl=self.settings.use_ssl,
            db=db,
            password=self.settings.redis_password,
            decode_responses=self.settings.redis_decode_responses
        )

    def test_connection(self) -> bool:
        try:
            return self.client.ping()
        except redis.exceptions.ConnectionError:
            return False

    def get_key_details(self, key: str, preview_mode: bool = False) -> RedisKey:
        """
        Helper method to get key details from Redis.

        Args:
            key: The Redis key to get details for
            preview_mode: If True, returns a preview of the data instead of the full value

        Returns:
            A RedisKey object with key details
        """
        key_type = self.client.type(key)
        if type(key_type) is bytes:
            key_type = key_type.decode('utf-8')
        ttl = self.client.ttl(key)
        value = None
        size = None
        preview = None

        # Get size and data based on key type
        if key_type == "string":
            value_data = self.client.get(key)
            size = len(value_data) if value_data else 0

            is_pickled, decoded_value = try_unpickle(value_data)

            if preview_mode:
                preview = str(decoded_value)[:100] if decoded_value else ""
            else:
                value = str(decoded_value)
        elif key_type == "list":
            size = self.client.llen(key)
            if preview_mode:
                preview = str(self.client.lrange(key, 0, 5))
            else:
                value = self.client.lrange(key, 0, -1)
        elif key_type == "hash":
            size = self.client.hlen(key)
            hash_data = self.client.hgetall(key)
            if preview_mode:
                preview = str(dict(list(hash_data.items())[:5]))
            else:
                value = hash_data
        elif key_type == "set":
            size = self.client.scard(key)
            set_data = self.client.smembers(key)
            if preview_mode:
                preview = str(list(set_data)[:5])
            else:
                value = list(set_data)
        elif key_type == "zset":
            size = self.client.zcard(key)
            if preview_mode:
                preview = str(self.client.zrange(key, 0, 5, withscores=True))
            else:
                value = self.client.zrange(key, 0, -1, withscores=True)

        # Create and return RedisKey with appropriate fields
        return RedisKey(
            key=key,
            type=key_type,
            ttl=ttl,
            size=size,
            preview=preview if preview_mode else None,
            value=value if not preview_mode else None
        )

    def get_keys(self, pattern: str = "*", limit: int = None) -> List[RedisKey]:
        """
        Get a list of keys matching the pattern with their info.

        Args:
            pattern: Redis key pattern to match
            limit: Maximum number of keys to return, defaults to settings.keys_limit

        Returns:
            List of RedisKey objects with preview data
        """
        # Use provided limit or default from settings
        if limit is None:
            limit = self.settings.keys_limit

        keys = self.client.keys(pattern)[:limit]
        return [self.get_key_details(key, preview_mode=True) for key in keys]


    def delete_key(self, key: str) -> bool:
        return bool(self.client.delete(key))

    def flush_db(self) -> bool:
        self.client.flushdb()
        return True

    def get_current_db(self) -> int:
        """Get the current database index."""
        return self.client.connection_pool.connection_kwargs.get('db', 0)

    def get_databases(self) -> List[Dict[str, Any]]:
        """Get a list of available Redis databases with key counts."""
        # Create a connection to database 0 to run the INFO command
        info_client = self._create_client(0)

        # Get database info from Redis INFO command
        info = info_client.info('keyspace')

        # Default Redis has 16 databases (0-15)
        # We can determine the actual number from the keyspace info
        max_db = 15  # Default max database index

        # Find the highest database index in the keyspace info
        for key in info.keys():
            if key.startswith('db'):
                try:
                    db_index = int(key[2:])  # Extract number from 'db0', 'db1', etc.
                    max_db = max(max_db, db_index)
                except ValueError:
                    pass

        # Create a list of all databases (even empty ones)
        databases = []
        current_db = self.get_current_db()

        for i in range(max_db + 1):
            db_key = f'db{i}'
            db_info = info.get(db_key, {})

            # If the database isn't in the info, it's empty
            keys = db_info.get('keys', 0)
            expires = db_info.get('expires', 0)

            databases.append({
                'index': i,
                'keys': keys,
                'expires': expires,
                'current': i == current_db
            })

        return databases

    def select_db(self, db_index: int) -> bool:
        try:
            self.client = self._create_client(db_index)
            self.db = db_index
            return self.test_connection()
        except Exception:
            return False

    def client_info(self) -> RedisInfo:
        """
        Fetch the raw INFO dictionary from Redis and return a validated RedisInfo model.
        Raises HTTPException(500) if the call fails for any reason.
        """
        try:
            raw_info: dict = self.client.info()
        except redis.exceptions.RedisError as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch INFO: {e}")

        # Parse into our Pydantic model (only fields defined in RedisInfo will be extracted).
        return RedisInfo.model_validate(raw_info)

    def get_slow_logs(self, count: int = 128) -> List[SlowLogEntry]:
        """
        Fetch up to `count` entries from Redis's slowlog.
        Each entry is a dict with keys: 'id', 'timestamp', 'execution_time', 'command'.
        Returns a list of such dicts, newest first.
        Raises HTTPException(500) if the call fails.
        """
        try:
            raw_list = self.client.slowlog_get(count)
        except redis.exceptions.RedisError as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch slowlog: {e}")

        validated: List[SlowLogEntry] = []
        for entry in raw_list:
            validated.append(SlowLogEntry.model_validate(entry))
        return validated


    def reset_slow_logs(self) -> bool:
        """
        Clear the Redis slowlog (SLOWLOG RESET).
        Returns True if successful, else raises HTTPException.
        """
        try:
            self.client.slowlog_reset()
            return True
        except redis.exceptions.RedisError as e:
            raise HTTPException(status_code=500, detail=f"Failed to reset slowlog: {e}")

    def execute_raw_command(self, command: str) -> Any:
        """
        Execute a raw Redis command.

        Args:
            command: The Redis command to execute (e.g., "GET mykey", "HGETALL myhash")

        Returns:
            The result of the command execution

        Raises:
            HTTPException: If the command execution fails
        """
        try:
            # Split the command into parts
            parts = command.split()
            if not parts:
                raise ValueError("Command cannot be empty")

            # Execute the command
            result = self.client.execute_command(*parts)

            # Handle different result types
            if isinstance(result, bytes):
                try:
                    # Try to decode as UTF-8
                    result = result.decode('utf-8')
                except UnicodeDecodeError:
                    # If it can't be decoded, return as hex
                    result = f"Binary data: {result.hex()}"

            # Try to detect and decode pickled data
            if isinstance(result, bytes) or isinstance(result, str):
                is_pickled, unpickled_value = try_unpickle(result)
                if is_pickled:
                    result = unpickled_value

            return result
        except redis.exceptions.RedisError as e:
            raise HTTPException(status_code=500, detail=f"Redis error: {e}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error executing command: {e}")


def get_redis_connection(db: int = None):
    conn = RedisConnection(db=db)
    if not conn.test_connection():
        raise HTTPException(status_code=500, detail="Cannot connect to Redis server")
    return conn

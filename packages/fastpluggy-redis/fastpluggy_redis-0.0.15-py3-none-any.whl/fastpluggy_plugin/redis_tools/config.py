from typing import Optional

from fastpluggy.core.config import BaseDatabaseSettings


class RedisToolsSettings(BaseDatabaseSettings):
    # Redis connection settings
    REDIS_DSN: Optional[str] = None

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    use_ssl: bool = False
    redis_password: Optional[str] = None
    redis_decode_responses: bool = False

    # Browser settings
    keys_limit: int = 100

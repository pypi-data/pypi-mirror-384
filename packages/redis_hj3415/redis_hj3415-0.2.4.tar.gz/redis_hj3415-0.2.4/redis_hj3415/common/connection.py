import os, redis
from redis.asyncio import Redis as AsyncRedis

from utils_hj3415 import setup_logger

mylogger = setup_logger(__name__)


# ─────────────────────────────
# Redis 연결 정보
# ─────────────────────────────
REDIS_ADDR = os.getenv('REDIS_ADDR', 'localhost')
REDIS_PASS = os.getenv('REDIS_PASS', None)

client: redis.Redis | None = None
async_client: AsyncRedis | None = None

# ─────────────────────────────
# 동기 Redis 클라이언트
# ─────────────────────────────
def get_redis_client(port: int = 6379) -> redis.Redis:
    global client
    if client is None:
        mylogger.info(f"[Redis] Connecting to sync Redis: host={REDIS_ADDR}, port={port}")
        client = redis.Redis(
            host=REDIS_ADDR,
            port=port,
            password=REDIS_PASS,
            decode_responses=True
        )
        try:
            client.ping()
            mylogger.info("[Redis] Sync Redis connection successful.")
        except redis.exceptions.ConnectionError as e:
            mylogger.error(f"[Redis] Sync connection failed: {e}")
            raise
    return client

# ─────────────────────────────
# 비동기 Redis 클라이언트
# ─────────────────────────────
def get_redis_client_async(port: int = 6379) -> AsyncRedis:
    global async_client
    if async_client is None:
        mylogger.info(f"[Redis] Connecting to async Redis: host={REDIS_ADDR}, port={port}")
        async_client = AsyncRedis(
            host=REDIS_ADDR,
            port=port,
            password=REDIS_PASS,
            decode_responses=True
        )
    return async_client
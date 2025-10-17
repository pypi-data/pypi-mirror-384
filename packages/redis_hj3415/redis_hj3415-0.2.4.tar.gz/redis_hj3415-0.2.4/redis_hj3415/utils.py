from typing import Iterable
import redis

from redis.asyncio import Redis as AsyncRedis
from .schemas import KeyWithTTL
from .common.connection import get_redis_client_async

from utils_hj3415 import setup_logger

mylogger = setup_logger(__name__)


BATCH_SIZE = 1000  # 상황에 맞게 조절

async def get_redis_keys_with_ttl(prefix: str = "") -> list[KeyWithTTL]:
    """
    Redis 키(prefix 매칭)와 TTL을 비동기/배치 파이프라인으로 조회.

    - 클라이언트는 decode_responses=True 로 문자열 키를 받는다고 가정.
    - TTL 의미:
        * -1: 만료 없음
        * -2: 키 없음 (SCAN 이후 삭제된 경우 가능)
    """
    r: AsyncRedis = get_redis_client_async()  # decode_responses=True 권장
    pattern = f"{prefix}*" if prefix else "*"

    results: list[KeyWithTTL] = []
    batch: list[str] = []

    # 1) 키 스캔 (count 힌트로 왕복 최적화)
    async for k in r.scan_iter(match=pattern, count=1000):
        batch.append(k)
        if len(batch) >= BATCH_SIZE:
            # 2) 배치 파이프라인으로 TTL 조회
            ttls = await _fetch_ttls_batch(r, batch)
            results.extend(KeyWithTTL(key=key, ttl=int(ttl)) for key, ttl in zip(batch, ttls))
            batch.clear()

    # 3) 남은 키 처리
    if batch:
        ttls = await _fetch_ttls_batch(r, batch)
        results.extend(KeyWithTTL(key=key, ttl=int(ttl)) for key, ttl in zip(batch, ttls))

    # 정렬(키 기준)
    results.sort(key=lambda x: x.key)
    return results


async def _fetch_ttls_batch(r: AsyncRedis, keys: Iterable[str]) -> list[int]:
    """주어진 키들에 대해 TTL을 파이프라인으로 조회 (transaction=False)."""
    async with r.pipeline(transaction=False) as pipe:
        for k in keys:
            pipe.ttl(k) # IDE경고 무시해도 됨
        return await pipe.execute()


async def delete_key(key: str) -> bool:
    """
    주어진 Redis 단일 키를 삭제합니다.(키이름이 일치해야함)

    Returns
    -------
    bool
        True : 키가 존재해 삭제됨 (DEL 결과 1)
        False: 키가 없었음 (DEL 결과 0) 또는 Redis 오류 발생
    """
    r: AsyncRedis = get_redis_client_async()
    try:
        deleted: int = await r.delete(key)  # 1: 삭제됨, 0: 없음
        return bool(deleted)
    except (redis.ConnectionError, redis.TimeoutError, redis.RedisError) as e:
        mylogger.warning("Redis DEL 실패: key=%s, err=%s", key, e)
        return False


async def delete_key_with_pattern(pattern_or_key: str, *, min_prefix: int = 3) -> int:
    """
    Redis 키(정확한 키 or 와일드카드 패턴)를 삭제한다.

    - 와일드카드 없음 → 단일 키 삭제 (DEL key)
    - 와일드카드 존재 → SCAN으로 매칭 키를 찾아 배치로 삭제 (UNLINK 또는 DEL)

    Parameters
    ----------
    pattern_or_key : str
        예) 'nbeats*', 'session:*', 'exact:key'
    min_prefix : int
        와일드카드 사용 시, 첫 와일드카드 앞의 prefix 최소 길이(안전장치)

    Returns
    -------
    int
        실제 삭제된(또는 언링크된) 키 개수
    """
    r: AsyncRedis = get_redis_client_async()

    # 패턴 여부 판단: Redis 글롭 문자인 '*', '?', '[]' 포함 여부
    is_glob = any(ch in pattern_or_key for ch in ("*", "?", "[", "]"))

    # 단일 키 삭제 경로
    if not is_glob:
        try:
            return int(await r.delete(pattern_or_key))
        except (redis.ConnectionError, redis.TimeoutError, redis.RedisError):
            return 0

    # 안전장치: 전체 삭제 위험 방지('*'만 넘기는 실수 등)
    # 첫 와일드카드 앞 prefix 길이 확인
    first_wc_idx = min(
        (i for i in (pattern_or_key.find("*"),
                     pattern_or_key.find("?"),
                     pattern_or_key.find("[")) if i != -1),
        default=-1
    )
    prefix = pattern_or_key if first_wc_idx == -1 else pattern_or_key[:first_wc_idx]
    if len(prefix) < min_prefix:
        raise ValueError(
            f"위험한 패턴입니다. 첫 와일드카드 앞 prefix 길이가 {min_prefix} 이상이어야 합니다: '{pattern_or_key}'"
        )

    # 매칭 키를 SCAN으로 찾고 배치 삭제
    deleter = r.unlink
    deleted = 0
    buf: list[str] = []

    try:
        # redis-py의 scan_iter는 async 제너레이터로 사용 가능
        async for key in r.scan_iter(match=pattern_or_key, count=1000):
            buf.append(key)
            if len(buf) >= 1000:
                deleted += int(await deleter(*buf))
                buf.clear()

        if buf:
            deleted += int(await deleter(*buf))
            buf.clear()

        return deleted

    except (redis.ConnectionError, redis.TimeoutError, redis.RedisError):
        return 0
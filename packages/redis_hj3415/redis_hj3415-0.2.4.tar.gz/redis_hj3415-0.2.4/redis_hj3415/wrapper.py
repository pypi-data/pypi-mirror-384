import hashlib
import functools
import inspect
import json
import os
import random
from datetime import timedelta

from typing import Any, Callable, Awaitable, TypeVar

from pydantic import BaseModel
from pydantic_core import to_jsonable_python  # pydantic v2 권장

from .common.connection import get_redis_client, get_redis_client_async


from utils_hj3415 import setup_logger

mylogger = setup_logger(__name__,'INFO')

# ─────────────────────────────────────────────────────────────────────────────
# 내부 정책용 JITTER(초) — 데코레이터 인자로 받지 않고 일괄 적용
# 운영 편의성을 위해 환경변수로 기본값만 조정 가능하게 합니다.
DEFAULT_JITTER_SECONDS = int(os.getenv("REDIS_JITTER_S", "300"))
# ─────────────────────────────────────────────────────────────────────────────
REDIS_EXPIRE_TIME_H = int(os.getenv("REDIS_EXPIRE_TIME_H", "12"))

def _make_key(tickers: list[str], trend: str) -> str:
    """티커 리스트 + 트렌드 → 16자리 해시 키 생성.

    - 티커는 소문자화 후 중복 제거, 정렬하여 순서/중복/대소문자 영향을 제거합니다.
    - 결과 형식: `<trend>:<sha1-16>`

    Args:
        tickers: 종목 코드 목록
        trend:   "up"/"down"/"상승"/"하락" 등 트렌드 문자열(정규화는 호출부 정책에 따름)

    Returns:
        예) "up:9b1de34a98c2a1f0"
    """
    norm = sorted(set(t.lower() for t in tickers))       # 정렬·중복 제거
    sha1 = hashlib.sha1(",".join(norm).encode()).hexdigest()[:16]
    return f"{trend}:{sha1}"                             # 짧고 충돌 낮음

def _json_default(o: Any):
    """JSON 직렬화 보조 함수.

    - 가능한 경우 pydantic v2의 `to_jsonable_python`을 우선 시도합니다.
    - 실패 시 `str(obj)`로 폴백합니다.
    """
    try:
        return to_jsonable_python(o)
    except Exception:
        return str(o)

def _seconds_from_ttl(ttl: Any) -> int | None:
    """TTL을 초 단위 정수로 정규화.

    지원 타입:
    - int/str 숫자 → int(seconds)
    - datetime.timedelta → int(total_seconds)
    - None 또는 잘못된 값 → None
    """
    if ttl is None:
        return None
    if isinstance(ttl, timedelta):
        return int(ttl.total_seconds())
    try:
        val = int(ttl)
        return val
    except Exception:
        return None

def _apply_jitter(base_ttl: int, jitter: int | tuple[int, int] | None) -> int:
    """TTL에 지터(초)를 더해 캐시 스탬피드를 완화합니다.

    - jitter가 int면 [0, jitter] 범위에서 난수 더함.
    - jitter가 (lo, hi)면 [max(0,lo), hi] 범위에서 난수 더함.
    - jitter가 0/None이거나 hi<=0이면 그대로 base_ttl 반환.
    """
    if not jitter:
        return base_ttl
    if isinstance(jitter, tuple):
        lo, hi = jitter
        if hi <= 0:
            return base_ttl
        return base_ttl + random.randint(max(0, lo), hi)
    # int
    if jitter <= 0:
        return base_ttl
    return base_ttl + random.randint(0, jitter)

def _safe_cache_key(cache_prefix: str, args: tuple, kwargs: dict) -> str:
    """기본 키 생성기: (args, kwargs)를 JSON 직렬화 후 SHA1 해시 8자리.

    - `sort_keys=True`로 dict 키 순서를 안정화합니다.
    - 리스트/튜플/세트의 '내용 순서'는 보존하므로, 순서가 달라지면 키도 달라집니다.
      (순서 무시 등 도메인 정규화가 필요하면 개별 `key_factory`를 사용하세요.)
    - 결과 형식: `<prefix>:<sha1-16>`
    """
    from hashlib import sha1
    payload = json.dumps(
        {"args": args, "kwargs": kwargs},
        default=str, ensure_ascii=False, sort_keys=True,
    )
    digest = sha1(payload.encode("utf-8")).hexdigest()[:8]
    return f"{cache_prefix}:{digest}"

def _env_default_ttl_seconds() -> int:
    """환경변수 `REDIS_EXPIRE_TIME_H`(기본 12시간)를 초 단위 TTL로 변환."""
    env_hours = REDIS_EXPIRE_TIME_H
    return env_hours * 60 * 60


# ─────────────────────────────────────────────────────────────────────────────
# 동기 캐시 데코레이터
# ─────────────────────────────────────────────────────────────────────────────

def redis_cached(
    *,
    prefix: str | None = None,
    default_if_miss: Any = None,
    ttl: int | timedelta | None = None,
    key_factory: Callable[[tuple, dict, str], str] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """동기 함수 결과를 Redis에 캐싱하는 데코레이터(간소화 버전).

    설계 포인트
    ----------
    - **간단한 인자**만 유지: `prefix`, `default_if_miss`, `ttl`, `key_factory`.
    - **jitter는 내부 정책**(`DEFAULT_JITTER_SECONDS`)으로 일괄 적용.
    - **호출 시 TTL 덮어쓰기(`ttl_kwarg`) 기능 제거**: TTL은 데코레이터 인자로만 설정.
    - 키 생성은 `key_factory`가 있으면 그걸 사용, 없으면 `_safe_cache_key` 사용.

    특수 kwargs (호출 시)
    ---------------------
    - refresh: bool = False  → True면 캐시 무시 후 실행/갱신.
    - cache_only: bool = False → True이고 MISS면 `default_if_miss`(callable이면 호출) 반환.

    Parameters
    ----------
    prefix : str | None
        Redis 키 prefix. 생략 시 함수 이름 사용.
    default_if_miss : Any
        `cache_only=True` + MISS 시 반환할 기본값(또는 호출 가능한 팩토리).
    ttl : int | timedelta | None
        기본 TTL. None이면 `REDIS_EXPIRE_TIME_H`(기본 12h)로부터 계산.
    key_factory : Callable
        키 생성 커스터마이저. 시그니처: `(args, kwargs, prefix) -> str`

    Returns
    -------
    Callable
        캐싱된 함수 래퍼.
    """
    env_default_ttl = _env_default_ttl_seconds()

    base_ttl = _seconds_from_ttl(ttl)
    if base_ttl is None:
        base_ttl = env_default_ttl

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        cache_prefix = prefix or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            refresh: bool = kwargs.pop("refresh", False)
            cache_only: bool = kwargs.pop("cache_only", False)

            final_ttl = _apply_jitter(base_ttl, DEFAULT_JITTER_SECONDS)
            redis_cli = get_redis_client()  # decode_responses=True 권장

            # 키 생성
            cache_key = key_factory(args, kwargs, cache_prefix) if key_factory \
                        else _safe_cache_key(cache_prefix, args, kwargs)

            # 1) 조회
            if not refresh:
                try:
                    raw = redis_cli.get(cache_key)
                    if raw is not None:
                        mylogger.info(f"[redis] HIT  {cache_key}")
                        raw_str = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
                        return json.loads(raw_str)
                except Exception as e:
                    mylogger.warning(f"[redis] GET 실패: {e}")

            # 2) cache_only 처리
            if cache_only and not refresh:
                mylogger.info(f"[redis] MISS {cache_key} → 기본값 반환")
                return default_if_miss() if callable(default_if_miss) else default_if_miss

            # 3) 원본 실행
            mylogger.info(f"[redis] RUN  {cache_key} (refresh={refresh})")
            result = func(*args, **kwargs)

            # 4) 갱신
            try:
                if final_ttl is not None and final_ttl > 0:
                    payload = json.dumps(
                        to_jsonable_python(result),
                        default=_json_default,
                        ensure_ascii=False,
                    )
                    redis_cli.setex(cache_key, final_ttl, payload)
                    mylogger.info(f"[redis] SETEX {cache_key} ({final_ttl}s)")
                else:
                    mylogger.info(f"[redis] SKIP SETEX {cache_key} (ttl={final_ttl})")
            except Exception as e:
                mylogger.warning(f"[redis] SETEX 실패: {e}")

            return result

        return wrapper
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# 비동기 캐시 데코레이터
# ─────────────────────────────────────────────────────────────────────────────

def redis_async_cached(
    *,
    prefix: str | None = None,
    default_if_miss: Any = None,
    ttl: int | timedelta | None = None,
    key_factory: Callable[[tuple, dict, str], str] | None = None,
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """비동기 함수 결과를 Redis에 캐싱하는 데코레이터(간소화 버전).

    설계 포인트 및 특수 kwargs는 `redis_cached`와 동일합니다.
    차이점은 비동기(await) I/O를 사용한다는 점뿐입니다.
    """
    env_default_ttl = _env_default_ttl_seconds()

    base_ttl = _seconds_from_ttl(ttl)
    if base_ttl is None:
        base_ttl = env_default_ttl

    def decorator(func: Callable[..., Awaitable[Any]]):
        if not inspect.iscoroutinefunction(func):
            raise TypeError("redis_async_cached 는 async 함수에만 사용할 수 있습니다.")

        cache_prefix = prefix or func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            refresh: bool = kwargs.pop("refresh", False)
            cache_only: bool = kwargs.pop("cache_only", False)

            final_ttl = _apply_jitter(base_ttl, DEFAULT_JITTER_SECONDS)
            redis_cli = get_redis_client_async()  # decode_responses=True 권장

            # 키 생성
            cache_key = key_factory(args, kwargs, cache_prefix) if key_factory \
                        else _safe_cache_key(cache_prefix, args, kwargs)

            # 1) 조회
            if not refresh:
                try:
                    raw = await redis_cli.get(cache_key)
                    if raw is not None:
                        mylogger.info(f"[redis] HIT  {cache_key}")
                        raw_str = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
                        return json.loads(raw_str)
                except Exception as e:
                    mylogger.warning(f"[redis] GET 실패: {e}")

            # 2) cache_only 처리
            if cache_only and not refresh:
                mylogger.info(f"[redis] MISS {cache_key} → 기본값 반환")
                return default_if_miss() if callable(default_if_miss) else default_if_miss

            # 3) 원본 실행
            mylogger.info(f"[redis] RUN  {cache_key} (refresh={refresh})")
            result = await func(*args, **kwargs)

            # 4) 갱신
            try:
                if final_ttl is not None and final_ttl > 0:
                    payload = json.dumps(
                        to_jsonable_python(result),
                        default=_json_default,
                        ensure_ascii=False,
                    )
                    await redis_cli.setex(cache_key, final_ttl, payload)
                    mylogger.info(f"[redis] SETEX {cache_key} ({final_ttl}s)")
                else:
                    mylogger.info(f"[redis] SKIP SETEX {cache_key} (ttl={final_ttl})")
            except Exception as e:
                mylogger.warning(f"[redis] SETEX 실패: {e}")

            return result

        return wrapper

    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic 모델/모델 리스트용 비동기 캐시 데코레이터
# ─────────────────────────────────────────────────────────────────────────────

M = TypeVar("M", bound=BaseModel)

def redis_async_cached_model(
    model: type[M],
    *,
    prefix: str | None = None,
    default_if_miss: Any = None,
    ttl: int | timedelta | None = None,
    key_factory: Callable[[tuple, dict, str], str] | None = None,
):
    """비동기 함수 결과(단일 Pydantic 모델 또는 모델 리스트)를 Redis에 캐싱.

    특징
    ----
    - 반환값이 `BaseModel` 또는 `list[BaseModel]`인 async 함수 전용.
    - 캐시 HIT 시:
        * 단일 모델: `model.model_validate_json(raw)`로 복원
        * 리스트: JSON 파싱 후 각 항목에 `model.model_validate(...)` 적용
        * 그 외 타입이 저장돼 있으면 그대로 반환(후방 호환)
    - 키 생성, refresh/cache_only, TTL/jitter 정책은 `redis_async_cached`와 동일.

    Parameters
    ----------
    model : type[M]
        복원에 사용할 Pydantic 모델 클래스.
    prefix : str | None
        Redis 키 prefix. 생략 시 함수 이름 사용.
    default_if_miss : Any
        `cache_only=True` + MISS 시 반환할 기본값(또는 호출 가능한 팩토리).
    ttl : int | timedelta | None
        기본 TTL. None이면 `REDIS_EXPIRE_TIME_H`(기본 12h)로부터 계산.
    key_factory : Callable
        키 생성 커스터마이저. 시그니처: `(args, kwargs, prefix) -> str`

    Returns
    -------
    Callable
        캐싱된 async 함수 래퍼.
    """
    env_default_ttl = _env_default_ttl_seconds()

    base_ttl = _seconds_from_ttl(ttl)
    if base_ttl is None:
        base_ttl = env_default_ttl

    def decorator(func: Callable[..., Awaitable[M] | Awaitable[list[M]]]):
        if not inspect.iscoroutinefunction(func):
            raise TypeError("redis_async_cached_model 데코레이터는 async 함수에만 사용 가능합니다.")

        cache_prefix = prefix or func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            refresh: bool = kwargs.pop("refresh", False)
            cache_only: bool = kwargs.pop("cache_only", False)

            final_ttl = _apply_jitter(base_ttl, DEFAULT_JITTER_SECONDS)
            redis_cli = get_redis_client_async()  # decode_responses=True 권장

            # 키 생성
            cache_key = key_factory(args, kwargs, cache_prefix) if key_factory \
                        else _safe_cache_key(cache_prefix, args, kwargs)

            # 1) 조회
            if not refresh:
                try:
                    raw = await redis_cli.get(cache_key)
                    if raw is not None:
                        mylogger.info(f"[redis] HIT  {cache_key}")
                        raw_str = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
                        # 단일 모델 시도
                        try:
                            return model.model_validate_json(raw_str)  # type: ignore[return-value]
                        except Exception:
                            # 리스트 시도
                            data = json.loads(raw_str)
                            if isinstance(data, list):
                                return [model.model_validate(d) for d in data]  # type: ignore[return-value]
                            return data
                except Exception as e:
                    mylogger.warning(f"[redis] GET 실패: {e}")

            # 2) cache_only 처리
            if cache_only and not refresh:
                mylogger.info(f"[redis] MISS {cache_key} → 기본값 반환")
                return default_if_miss() if callable(default_if_miss) else default_if_miss

            # 3) 원본 실행
            result = await func(*args, **kwargs)

            # 4) 갱신
            try:
                if final_ttl is not None and final_ttl > 0:
                    if isinstance(result, list):
                        if result and isinstance(result[0], BaseModel):
                            payload = json.dumps([m.model_dump(mode="json") for m in result], ensure_ascii=False)
                        else:
                            payload = json.dumps(to_jsonable_python(result), default=_json_default, ensure_ascii=False)
                    elif isinstance(result, BaseModel):
                        payload = result.model_dump_json()
                    else:
                        payload = json.dumps(to_jsonable_python(result), default=_json_default, ensure_ascii=False)

                    await redis_cli.setex(cache_key, final_ttl, payload)
                    mylogger.info(f"[redis] SETEX {cache_key} ({final_ttl}s)")
                else:
                    mylogger.info(f"[redis] SKIP SETEX {cache_key} (ttl={final_ttl})")
            except Exception as e:
                mylogger.warning(f"[redis] SETEX 실패: {e}")

            return result

        return wrapper
    return decorator
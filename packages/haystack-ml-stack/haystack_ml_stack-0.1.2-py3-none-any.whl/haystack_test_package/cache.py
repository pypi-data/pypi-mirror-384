from typing import Any

from cachetools import TLRUCache


def _ttu(_, value: Any, now: float) -> float:
    """Time-To-Use policy: allow per-item TTL via 'cache_ttl_in_seconds' or fallback."""
    ONE_YEAR = 365 * 24 * 60 * 60
    try:
        ttl = int(value.get("cache_ttl_in_seconds", -1))
        if ttl > 0:
            return now + ttl
    except Exception:
        pass
    return now + ONE_YEAR


def make_features_cache(maxsize: int) -> TLRUCache:
    return TLRUCache(maxsize=maxsize, ttu=_ttu)

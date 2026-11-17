"""Domain-age lookup with a cache and rate limits, so a public app cannot be used to flood RDAP.

Nothing here is written to disk. The cache holds only domain names and dates, in memory.
"""
from __future__ import annotations

import threading
import time
from collections import OrderedDict, deque
from dataclasses import dataclass
from datetime import date
from typing import Callable, Deque, Optional, Tuple

import rdap

CACHE_SECONDS_FOUND = 7 * 24 * 3600      # reuse a lookup that found a date for 7 days
CACHE_SECONDS_NOT_FOUND = 24 * 3600      # reuse a lookup that found nothing for 1 day
MAX_CACHE_ENTRIES = 2000


class SlidingWindowLimiter:
    """Allows at most max_calls within any window of window_seconds."""

    def __init__(self, max_calls: int, window_seconds: float, clock: Callable[[], float] = time.monotonic):
        self.max_calls = max_calls
        self.window = window_seconds
        self._clock = clock
        self._calls: Deque[float] = deque()
        self._lock = threading.Lock()

    def allow(self) -> bool:
        now = self._clock()
        with self._lock:
            while self._calls and now - self._calls[0] >= self.window:
                self._calls.popleft()
            if len(self._calls) >= self.max_calls:
                return False
            self._calls.append(now)
            return True


class DomainAgeCache:
    """A small in-memory cache: domain -> registration date (or None when it could not be found)."""

    def __init__(self, clock: Callable[[], float] = time.time, max_entries: int = MAX_CACHE_ENTRIES):
        self._clock = clock
        self._max = max_entries
        self._items: "OrderedDict[str, Tuple[Optional[date], float]]" = OrderedDict()
        self._lock = threading.Lock()

    def get(self, domain: str) -> Tuple[bool, Optional[date]]:
        with self._lock:
            item = self._items.get(domain)
            if item is None:
                return False, None
            registered, stored_at = item
            ttl = CACHE_SECONDS_FOUND if registered else CACHE_SECONDS_NOT_FOUND
            if self._clock() - stored_at > ttl:
                del self._items[domain]
                return False, None
            return True, registered

    def put(self, domain: str, registered: Optional[date]) -> None:
        with self._lock:
            self._items[domain] = (registered, self._clock())
            self._items.move_to_end(domain)
            while len(self._items) > self._max:
                self._items.popitem(last=False)


@dataclass
class LookupResult:
    age_days: Optional[int]
    status: str      # "ok", "cached", "unknown", "limited" or "off"
    fetched: bool    # True if a request really went out to the network


class AgeLookup:
    def __init__(
        self,
        fetch: Optional[Callable[[str], Optional[date]]],
        limiter: SlidingWindowLimiter,
        cache: Optional[DomainAgeCache] = None,
    ):
        """fetch=None turns the lookup off (nothing is ever sent outside)."""
        self._fetch = fetch
        self._limiter = limiter
        self._cache = cache or DomainAgeCache()

    @property
    def enabled(self) -> bool:
        return self._fetch is not None

    def lookup(self, domain: str, today: Optional[date] = None) -> LookupResult:
        if self._fetch is None:
            return LookupResult(None, "off", False)

        key = rdap.registrable_domain(domain)
        found, registered = self._cache.get(key)
        fetched = False
        if not found:
            if not self._limiter.allow():
                return LookupResult(None, "limited", False)
            registered = self._fetch(key)
            fetched = True
            self._cache.put(key, registered)

        if registered is None:
            return LookupResult(None, "unknown", fetched)
        days = max(((today or date.today()) - registered).days, 0)
        return LookupResult(days, "ok" if fetched else "cached", fetched)

import unittest
from datetime import date, timedelta

from lookup import (
    CACHE_SECONDS_FOUND,
    CACHE_SECONDS_NOT_FOUND,
    AgeLookup,
    DomainAgeCache,
    SlidingWindowLimiter,
)


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class LimiterTest(unittest.TestCase):
    def test_blocks_after_limit_and_recovers(self):
        clock = FakeClock()
        limiter = SlidingWindowLimiter(2, 60, clock=clock)
        self.assertTrue(limiter.allow())
        self.assertTrue(limiter.allow())
        self.assertFalse(limiter.allow())
        clock.now += 61
        self.assertTrue(limiter.allow())


class CacheTest(unittest.TestCase):
    def test_found_and_missing_have_different_lifetimes(self):
        clock = FakeClock()
        cache = DomainAgeCache(clock=clock)
        cache.put("a.example", date(2020, 1, 1))
        cache.put("b.example", None)
        clock.now += CACHE_SECONDS_NOT_FOUND + 1
        self.assertEqual(cache.get("a.example"), (True, date(2020, 1, 1)))
        self.assertEqual(cache.get("b.example"), (False, None))
        clock.now += CACHE_SECONDS_FOUND
        self.assertEqual(cache.get("a.example"), (False, None))

    def test_oldest_entries_are_dropped(self):
        cache = DomainAgeCache(max_entries=2)
        cache.put("a.example", None)
        cache.put("b.example", None)
        cache.put("c.example", None)
        self.assertEqual(cache.get("a.example"), (False, None))
        self.assertTrue(cache.get("c.example")[0])


class AgeLookupTest(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.today = date(2026, 11, 17)

    def fetch(self, domain):
        self.calls.append(domain)
        return self.today - timedelta(days=10)

    def test_lookup_uses_registrable_domain_and_cache(self):
        lookup = AgeLookup(self.fetch, SlidingWindowLimiter(10, 60))
        first = lookup.lookup("mail.shop.example.com", today=self.today)
        second = lookup.lookup("www.example.com", today=self.today)
        self.assertEqual(first.age_days, 10)
        self.assertEqual((first.status, first.fetched), ("ok", True))
        self.assertEqual((second.status, second.fetched), ("cached", False))
        self.assertEqual(self.calls, ["example.com"])

    def test_limit_stops_network_calls(self):
        lookup = AgeLookup(self.fetch, SlidingWindowLimiter(1, 60))
        lookup.lookup("a.example", today=self.today)
        blocked = lookup.lookup("b.example", today=self.today)
        self.assertEqual((blocked.age_days, blocked.status, blocked.fetched), (None, "limited", False))
        self.assertEqual(self.calls, ["a.example"])

    def test_off_never_calls_out(self):
        lookup = AgeLookup(None, SlidingWindowLimiter(10, 60))
        result = lookup.lookup("a.example", today=self.today)
        self.assertEqual((result.age_days, result.status, result.fetched), (None, "off", False))
        self.assertFalse(lookup.enabled)

    def test_not_found_is_reported_as_unknown(self):
        lookup = AgeLookup(lambda d: None, SlidingWindowLimiter(10, 60))
        self.assertEqual(lookup.lookup("a.example").status, "unknown")


if __name__ == "__main__":
    unittest.main()

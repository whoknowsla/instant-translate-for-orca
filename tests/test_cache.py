from instant_translate.cache import TranslationCache


def _key(text):
    return ("google", "auto", "en", text)


def test_cache_evicts_least_recently_used_entry():
    cache = TranslationCache(max_entries=2, max_bytes=1000)
    cache[_key("one")] = "1"
    cache[_key("two")] = "2"
    assert cache[_key("one")] == "1"  # make one most recently used
    cache[_key("three")] = "3"
    assert _key("one") in cache
    assert _key("two") not in cache


def test_cache_respects_byte_budget():
    cache = TranslationCache(max_entries=10, max_bytes=45)
    cache[_key("a")] = "small"
    cache[_key("b")] = "x" * 30
    assert cache.size_bytes <= cache.max_bytes


def test_single_oversized_entry_is_not_cached():
    cache = TranslationCache(max_entries=10, max_bytes=10)
    cache[_key("large")] = "x" * 100
    assert len(cache) == 0

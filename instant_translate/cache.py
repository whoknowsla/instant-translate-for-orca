# Copyright (C) 2026 the Instant Translate for Orca contributors.
#
# SPDX-License-Identifier: GPL-2.0-only
"""Memory-bounded translation result cache."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterator, MutableMapping

CacheKey = tuple[str, str, str, str]


class TranslationCache(MutableMapping[CacheKey, str]):
    """An LRU cache bounded by both entry count and approximate UTF-8 bytes."""

    def __init__(self, *, max_entries: int = 200, max_bytes: int = 2 * 1024 * 1024) -> None:
        if max_entries <= 0 or max_bytes <= 0:
            raise ValueError("cache bounds must be positive")
        self.max_entries = max_entries
        self.max_bytes = max_bytes
        self._entries: OrderedDict[CacheKey, str] = OrderedDict()
        self._size_bytes = 0

    @staticmethod
    def _entry_size(key: CacheKey, value: str) -> int:
        return sum(len(part.encode("utf-8")) for part in key) + len(value.encode("utf-8"))

    @property
    def size_bytes(self) -> int:
        return self._size_bytes

    def __getitem__(self, key: CacheKey) -> str:
        value = self._entries[key]
        self._entries.move_to_end(key)
        return value

    def __setitem__(self, key: CacheKey, value: str) -> None:
        if key in self._entries:
            old_value = self._entries.pop(key)
            self._size_bytes -= self._entry_size(key, old_value)

        size = self._entry_size(key, value)
        if size > self.max_bytes:
            return

        self._entries[key] = value
        self._size_bytes += size
        while len(self._entries) > self.max_entries or self._size_bytes > self.max_bytes:
            old_key, old_value = self._entries.popitem(last=False)
            self._size_bytes -= self._entry_size(old_key, old_value)

    def __delitem__(self, key: CacheKey) -> None:
        value = self._entries.pop(key)
        self._size_bytes -= self._entry_size(key, value)

    def __iter__(self) -> Iterator[CacheKey]:
        return iter(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()
        self._size_bytes = 0

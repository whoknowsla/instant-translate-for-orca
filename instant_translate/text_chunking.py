# Copyright (C) 2026 the Instant Translate for Orca contributors.
# Based on YandexTranslate for NVDA's smartsplit() by alekssamos
# (https://github.com/alekssamos/YandexTranslate), MIT licensed.
#
# This file is covered by the GNU General Public License, version 2.
# See the LICENSE file for details.
#
# SPDX-License-Identifier: GPL-2.0-only
"""Word-boundary-aware text chunking shared by the Yandex and DeepL backends.

Unlike Google's sentence-punctuation-based ``split_chunks`` in
``google_chunking.py``, Yandex and DeepL's request-size limits are best respected
by breaking on whitespace so words are never cut in half, falling back to a
hard break only when no whitespace is available in range.
"""

from __future__ import annotations

from collections.abc import Iterator

_BREAK_CHARS = frozenset({" ", "\t", "\n", "\xa0"})


def iter_smart_chunks(text: str, min_len: int, max_len: int) -> Iterator[str]:
    """Yield bounded chunks while retaining the original splitting behavior."""

    if min_len < 0 or max_len <= 0 or min_len >= max_len:
        raise ValueError("expected 0 <= min_len < max_len")

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if max_len >= len(text):
        yield text
        return

    current: list[str] = []
    count = 0
    for char in text:
        count += 1
        current.append(char)
        if count < min_len:
            continue
        if count == max_len:
            yield "".join(current)
            current = []
            count = 0
            continue
        if min_len < count < max_len and char in _BREAK_CHARS:
            yield "".join(current)
            current = []
            count = 0
    if current:
        yield "".join(current)


def smart_split(text: str, min_len: int, max_len: int) -> list[str]:
    """Splits text into chunks no shorter than min_len (except the last)
    and no longer than max_len, preferring to break at whitespace.
    """

    return list(iter_smart_chunks(text, min_len, max_len))

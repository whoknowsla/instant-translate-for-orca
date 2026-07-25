# Copyright (C) 2013-2024 Mesar Hameed <mhameed@src.gnome.org>, Beqa Gozalishvili,
# and other NVDA Instant Translate contributors.
# Copyright (C) 2026 the Instant Translate for Orca contributors.
#
# This file is covered by the GNU General Public License, version 2.
# See the LICENSE file for details.
#
# SPDX-License-Identifier: GPL-2.0-only
"""Legacy sentence-punctuation chunking used by the Google backend."""

from __future__ import annotations

import re

_ARABIC_BREAKS = "[،؛؟]"
_CHINESE_BREAKS = "[　-〿︐-︟︰-﹯！-｠]"
_LATIN_BREAKS = r"[.,!?;:]"
_SPLIT_RE = re.compile(f"{_ARABIC_BREAKS}|{_CHINESE_BREAKS}|{_LATIN_BREAKS}")


def split_chunks(text: str, chunk_size: int):
    """Yields text split into pieces no larger than chunk_size where possible.

    Splits are only made at sentence-ending punctuation so words are never
    cut in half.
    """

    pos = 0
    potential_pos = 0
    for mark in _SPLIT_RE.finditer(text):
        if (mark.start() - pos + 1) < chunk_size:
            potential_pos = mark.start()
            continue
        yield text[pos:potential_pos + 1]
        pos = potential_pos + 1
        potential_pos = mark.start()
    yield text[pos:]

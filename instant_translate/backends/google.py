# Copyright (C) 2026 the Instant Translate for Orca contributors.
#
# SPDX-License-Identifier: GPL-2.0-only
"""Google public-endpoint backend.

The caller supplies the legacy splitter. This deliberately preserves its
existing behavior, including an unlimited number of sequential chunks.
"""

from __future__ import annotations

import threading
import urllib.parse
from collections.abc import Callable, Iterable

from ..http_client import JsonHttpClient
from ..models import TranslationRequest, TranslationResult
from .base import exception_result

_LANG_FIXUPS = {"iw": "he", "jw": "jv"}
_DEFAULT_URL = "https://translate.googleapis.com/translate_a/single"
_MIRROR_URL = "https://translate.googleapis.mirror.nvdadr.com/translate_a/single"


class GoogleBackend:
    """Synchronous adapter for Google's undocumented public endpoint."""

    def __init__(
        self,
        splitter: Callable[[str, int], Iterable[str]],
        *,
        chunk_size: int = 3000,
        opener=None,
    ) -> None:
        self.splitter = splitter
        self.chunk_size = chunk_size
        self.client = JsonHttpClient(opener=opener)
        if hasattr(self.client.opener, "addheaders"):
            self.client.opener.addheaders = [("User-agent", "Mozilla/5.0")]

    def translate(
        self,
        request: TranslationRequest,
        cancel_event: threading.Event | None = None,
    ) -> TranslationResult:
        template = (_MIRROR_URL if request.use_mirror else _DEFAULT_URL) + (
            "?client=gtx&sl={lang_from}&tl={lang_to}&dt=t&q={text}&dj=1"
        )
        translated_parts: list[str] = []
        detected = ""
        try:
            # Do not cap or otherwise alter Google chunk generation: users may
            # intentionally translate text requiring many sequential requests.
            for chunk in self.splitter(request.text, self.chunk_size):
                if cancel_event is not None and cancel_event.is_set():
                    return TranslationResult.cancelled_result()
                url = template.format(
                    lang_from=request.source_language,
                    lang_to=request.target_language,
                    text=urllib.parse.quote(chunk.encode("utf-8")),
                )
                payload = self.client.open_json(
                    url,
                    timeout=15,
                    cancel_event=cancel_event,
                )
                source = payload["src"]
                detected = _LANG_FIXUPS.get(source, source)
                translated_parts.append(
                    "".join(sentence["trans"] for sentence in payload["sentences"])
                )
        except Exception as exc:  # noqa: BLE001 - converted to a typed, redacted result.
            return exception_result("Google Translate", exc)
        return TranslationResult("".join(translated_parts), detected)

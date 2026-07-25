# Copyright (C) 2026 the Instant Translate for Orca contributors.
#
# SPDX-License-Identifier: GPL-2.0-only
"""Official DeepL API backend."""

from __future__ import annotations

import threading
import urllib.parse
import urllib.request
from typing import ClassVar

from ..http_client import JsonHttpClient
from ..i18n import _
from ..models import ErrorKind, TranslationRequest, TranslationResult
from ..text_chunking import iter_smart_chunks
from .base import RequestDeadline, exception_result


class DeepLBackend:
    ERRORS: ClassVar[dict[int, str]] = {
        400: _("DeepL rejected the request as malformed."),
        403: _("The DeepL API key is invalid."),
        429: _("Too many requests to DeepL. Please wait and try again."),
        456: _("The DeepL translation quota has been exceeded."),
    }
    FREE_URL = "https://api-free.deepl.com/v2/translate"
    PRO_URL = "https://api.deepl.com/v2/translate"
    MAX_INPUT_CHARACTERS = 100_000
    TOTAL_TIMEOUT_SECONDS = 120

    def __init__(self, api_key: str, plan: str = "free", *, opener=None) -> None:
        self.api_key = api_key
        self.plan = plan if plan in {"free", "pro"} else "free"
        self.client = JsonHttpClient(opener=opener)

    @property
    def endpoint(self) -> str:
        return self.FREE_URL if self.plan == "free" else self.PRO_URL

    def _translate_chunk(
        self,
        request: TranslationRequest,
        chunk: str,
        cancel_event: threading.Event | None,
        timeout: float,
    ) -> dict:
        params = {"text": chunk, "target_lang": request.target_language}
        if request.source_language != "auto":
            params["source_lang"] = request.source_language
        http_request = urllib.request.Request(
            self.endpoint,
            data=urllib.parse.urlencode(params).encode("utf-8"),
            headers={
                "Authorization": f"DeepL-Auth-Key {self.api_key}",
                "User-Agent": "Instant Translate for Orca",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )
        return self.client.open_json(
            http_request,
            timeout=timeout,
            cancel_event=cancel_event,
        )

    def translate(
        self,
        request: TranslationRequest,
        cancel_event: threading.Event | None = None,
    ) -> TranslationResult:
        if len(request.text) > self.MAX_INPUT_CHARACTERS:
            return TranslationResult.failure(
                ErrorKind.INVALID_REQUEST,
                _("DeepL input is limited to {maximum:,} characters.").format(
                    maximum=self.MAX_INPUT_CHARACTERS
                ),
            )
        translated_parts: list[str] = []
        detected = ""
        deadline = RequestDeadline(self.TOTAL_TIMEOUT_SECONDS)
        try:
            # The 5,500-character bound remains well below DeepL's 128 KiB
            # encoded request ceiling even for three-byte UTF-8 scripts.
            for chunk in iter_smart_chunks(request.text, 5000, 5500):
                if cancel_event is not None and cancel_event.is_set():
                    return TranslationResult.cancelled_result()
                payload = self._translate_chunk(
                    request,
                    chunk,
                    cancel_event,
                    deadline.timeout(),
                )
                translations = payload.get("translations") or []
                if not translations:
                    return TranslationResult.failure(
                        ErrorKind.MALFORMED_RESPONSE,
                        _("DeepL returned an invalid response."),
                        diagnostic="MissingTranslations",
                    )
                first = translations[0]
                translated_parts.append(first["text"])
                detected = first.get("detected_source_language", "").lower() or detected
        except Exception as exc:  # noqa: BLE001 - converted to a typed, redacted result.
            return exception_result("DeepL", exc, http_messages=self.ERRORS)
        return TranslationResult("".join(translated_parts), detected)

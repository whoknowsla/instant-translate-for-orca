# Copyright (C) 2026 the Instant Translate for Orca contributors.
#
# SPDX-License-Identifier: GPL-2.0-only
"""Yandex unofficial iOS-endpoint backend."""

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


class YandexBackend:
    ERRORS: ClassVar[dict[int, str]] = {
        401: _("Invalid Yandex Translate access key."),
        402: _("This Yandex Translate access key has been blocked."),
        403: _("You have reached Yandex Translate's daily request limit."),
        404: _("You have reached Yandex Translate's daily translated-text limit."),
        405: _("Yandex Translate rejected the request method."),
        413: _("The text is too large to translate in one request."),
        422: _("Yandex Translate could not translate this text."),
        501: _("Yandex Translate does not support this language direction."),
    }
    API_URL = "https://translate.yandex.net/api/v1/tr.json/translate"
    UCID = "9676696D-0B56-4F13-B4D5-4A3DA2A3344D"
    SID = "1A5A10A952AB4A3B82533F44B87EE696"
    ID = f"{SID}-0-0"
    MAX_INPUT_CHARACTERS = 100_000
    TOTAL_TIMEOUT_SECONDS = 120
    ERROR_KINDS: ClassVar[dict[int, ErrorKind]] = {
        401: ErrorKind.AUTHENTICATION,
        402: ErrorKind.AUTHENTICATION,
        403: ErrorKind.QUOTA,
        404: ErrorKind.QUOTA,
        405: ErrorKind.INVALID_REQUEST,
        413: ErrorKind.INVALID_REQUEST,
        422: ErrorKind.INVALID_REQUEST,
        501: ErrorKind.UNSUPPORTED_LANGUAGE,
    }

    def __init__(self, *, opener=None) -> None:
        self.client = JsonHttpClient(opener=opener)

    def _translate_chunk(
        self,
        chunk: str,
        lang_param: str,
        cancel_event: threading.Event | None,
        timeout: float,
    ) -> tuple[str, str, int]:
        query = urllib.parse.urlencode(
            {
                "id": self.ID,
                "srv": "ios",
                "ucid": self.UCID,
                "sid": self.SID,
                "lang": lang_param,
            }
        )
        http_request = urllib.request.Request(
            f"{self.API_URL}?{query}",
            data=urllib.parse.urlencode({"text": chunk}).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        payload = self.client.open_json(
            http_request,
            timeout=timeout,
            cancel_event=cancel_event,
        )
        code = payload.get("code", 200)
        if code != 200:
            return "", "", code
        lang_value = payload.get("lang", "")
        detected = lang_value.split("-", 1)[0] if "-" in lang_value else ""
        return "".join(payload.get("text", [])), detected, code

    def translate(
        self,
        request: TranslationRequest,
        cancel_event: threading.Event | None = None,
    ) -> TranslationResult:
        if len(request.text) > self.MAX_INPUT_CHARACTERS:
            return TranslationResult.failure(
                ErrorKind.INVALID_REQUEST,
                _("Yandex Translate input is limited to {maximum:,} characters.").format(
                    maximum=self.MAX_INPUT_CHARACTERS
                ),
            )
        lang_param = (
            request.target_language
            if request.source_language == "auto"
            else f"{request.source_language}-{request.target_language}"
        )
        translated_parts: list[str] = []
        detected = ""
        deadline = RequestDeadline(self.TOTAL_TIMEOUT_SECONDS)
        try:
            for chunk in iter_smart_chunks(request.text, 500, 550):
                if cancel_event is not None and cancel_event.is_set():
                    return TranslationResult.cancelled_result()
                translated, chunk_detected, code = self._translate_chunk(
                    chunk,
                    lang_param,
                    cancel_event,
                    deadline.timeout(),
                )
                if code != 200:
                    return TranslationResult.failure(
                        self.ERROR_KINDS.get(code, ErrorKind.UNKNOWN),
                        self.ERRORS.get(
                            code,
                            _("Yandex Translate failed (code {code}).").format(code=code),
                        ),
                        diagnostic=f"ProviderCode:{code}",
                    )
                translated_parts.append(translated)
                detected = chunk_detected or detected
        except Exception as exc:  # noqa: BLE001 - converted to a typed, redacted result.
            return exception_result(
                "Yandex Translate",
                exc,
                http_messages=self.ERRORS,
                http_kinds=self.ERROR_KINDS,
            )
        return TranslationResult("".join(translated_parts), detected)

# Copyright (C) 2026 the Instant Translate for Orca contributors.
#
# SPDX-License-Identifier: GPL-2.0-only
"""Small, bounded urllib JSON client shared by translation providers."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from email.message import Message


class ResponseTooLargeError(ValueError):
    """Raised before parsing a response beyond the configured byte limit."""


class RequestCancelledError(RuntimeError):
    """Raised when cooperative cancellation interrupts retry/backoff work."""


class JsonHttpClient:
    """Performs verified HTTPS requests with bounded responses and retries."""

    def __init__(
        self,
        *,
        opener=None,
        max_response_bytes: int = 1024 * 1024,
        max_attempts: int = 3,
    ) -> None:
        self.opener = opener or urllib.request.build_opener()
        self.max_response_bytes = max_response_bytes
        self.max_attempts = max_attempts

    def open_json(
        self,
        request,
        *,
        timeout: float = 15,
        cancel_event: threading.Event | None = None,
    ):
        for attempt in range(self.max_attempts):
            if cancel_event is not None and cancel_event.is_set():
                raise RequestCancelledError
            try:
                with self.opener.open(request, timeout=timeout) as response:
                    return self._read_json(response)
            except urllib.error.HTTPError as exc:
                if exc.code not in {429, 500, 502, 503, 504} or attempt + 1 >= self.max_attempts:
                    raise
                delay = self._retry_delay(exc.headers, attempt)
                exc.close()
                if cancel_event is not None:
                    if cancel_event.wait(delay):
                        raise RequestCancelledError from exc
                else:
                    threading.Event().wait(delay)
        raise AssertionError("retry loop exhausted unexpectedly")

    def _read_json(self, response):
        content_length = self._content_length(getattr(response, "headers", None))
        if content_length is not None and content_length > self.max_response_bytes:
            raise ResponseTooLargeError
        raw = response.read(self.max_response_bytes + 1)
        if len(raw) > self.max_response_bytes:
            raise ResponseTooLargeError
        return json.loads(raw.decode("utf-8"))

    @staticmethod
    def _content_length(headers: Message | None) -> int | None:
        if headers is None:
            return None
        value = headers.get("Content-Length")
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _retry_delay(headers: Message | None, attempt: int) -> float:
        retry_after = headers.get("Retry-After") if headers is not None else None
        try:
            if retry_after is not None:
                return min(max(float(retry_after), 0.0), 10.0)
        except ValueError:
            pass
        return min(0.5 * (2**attempt), 2.0)

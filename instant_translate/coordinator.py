# Copyright (C) 2026 the Instant Translate for Orca contributors.
#
# SPDX-License-Identifier: GPL-2.0-only
"""Bounded latest-request background execution."""

from __future__ import annotations

import threading
from collections.abc import Callable

from .i18n import _
from .models import ErrorKind, TranslationRequest, TranslationResult

Execute = Callable[[TranslationRequest, threading.Event], TranslationResult]
Done = Callable[[int, TranslationRequest, TranslationResult, bool], None]


class LatestRequestCoordinator:
    """Runs at most one request and retains at most one pending request.

    Submitting a newer request cancels the active request cooperatively and
    replaces any request that has not started. Completion callbacks identify
    whether a result is still the most recently submitted request.
    """

    def __init__(self, execute: Execute, on_done: Done) -> None:
        self._execute = execute
        self._on_done = on_done
        self._condition = threading.Condition()
        self._pending: tuple[int, TranslationRequest] | None = None
        self._active_cancel: threading.Event | None = None
        self._latest_id = 0
        self._closed = False
        self._thread = threading.Thread(
            target=self._run,
            name="instant-translate-worker",
            daemon=True,
        )
        self._thread.start()

    def submit(self, request: TranslationRequest) -> int:
        with self._condition:
            if self._closed:
                raise RuntimeError("translation coordinator is closed")
            self._latest_id += 1
            request_id = self._latest_id
            if self._active_cancel is not None:
                self._active_cancel.set()
            self._pending = (request_id, request)
            self._condition.notify()
            return request_id

    def supersede(self) -> None:
        """Cancel active/pending work when a cache hit becomes the newest result."""

        with self._condition:
            if self._closed:
                return
            self._latest_id += 1
            self._pending = None
            if self._active_cancel is not None:
                self._active_cancel.set()

    def is_latest(self, request_id: int) -> bool:
        """Return whether a result is still current at presentation time."""

        with self._condition:
            return not self._closed and request_id == self._latest_id

    def _run(self) -> None:
        while True:
            with self._condition:
                while self._pending is None and not self._closed:
                    self._condition.wait()
                if self._closed:
                    return
                pending = self._pending
                if pending is None:
                    continue
                request_id, request = pending
                self._pending = None
                cancel_event = threading.Event()
                self._active_cancel = cancel_event

            try:
                result = self._execute(request, cancel_event)
            except Exception as exc:  # noqa: BLE001 - last containment boundary for Orca.
                result = TranslationResult.failure(
                    kind=ErrorKind.UNKNOWN,
                    message=_("Translation failed because of an internal error."),
                    diagnostic=type(exc).__name__,
                )

            with self._condition:
                is_latest = not self._closed and request_id == self._latest_id
                if self._active_cancel is cancel_event:
                    self._active_cancel = None

            self._on_done(request_id, request, result, is_latest)

    def close(self) -> None:
        with self._condition:
            self._closed = True
            self._pending = None
            if self._active_cancel is not None:
                self._active_cancel.set()
            self._condition.notify_all()

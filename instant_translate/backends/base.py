# Copyright (C) 2026 the Instant Translate for Orca contributors.
#
# SPDX-License-Identifier: GPL-2.0-only
"""Shared provider error conversion."""

from __future__ import annotations

import json
import ssl
import time
import urllib.error
from collections.abc import Mapping

from ..http_client import RequestCancelledError, ResponseTooLargeError
from ..i18n import _
from ..models import ErrorKind, TranslationResult


class RequestDeadline:
    """Provide per-call timeouts constrained by a total operation deadline."""

    def __init__(self, total_seconds: float) -> None:
        self._expires_at = time.monotonic() + total_seconds

    def timeout(self, maximum: float = 15) -> float:
        remaining = self._expires_at - time.monotonic()
        if remaining <= 0:
            raise TimeoutError
        return min(maximum, remaining)


def exception_result(
    provider: str,
    exc: Exception,
    *,
    http_messages: Mapping[int, str] | None = None,
    http_kinds: Mapping[int, ErrorKind] | None = None,
) -> TranslationResult:
    """Map an exception to a redacted provider-specific result."""

    if isinstance(exc, RequestCancelledError):
        return TranslationResult.cancelled_result()
    if isinstance(exc, ResponseTooLargeError):
        return TranslationResult.failure(
            ErrorKind.RESPONSE_TOO_LARGE,
            _("{provider} returned an unexpectedly large response.").format(
                provider=provider
            ),
            diagnostic="ResponseTooLargeError",
        )
    if isinstance(exc, urllib.error.HTTPError):
        code = exc.code
        message = (http_messages or {}).get(
            code,
            _("{provider} request failed (HTTP {code}).").format(
                provider=provider,
                code=code,
            ),
        )
        if http_kinds and code in http_kinds:
            kind = http_kinds[code]
        elif code in {401, 402, 403}:
            kind = ErrorKind.AUTHENTICATION
        elif code in {404, 456}:
            kind = ErrorKind.QUOTA
        elif code == 429:
            kind = ErrorKind.RATE_LIMIT
        elif code == 422:
            kind = ErrorKind.INVALID_REQUEST
        elif code == 501:
            kind = ErrorKind.UNSUPPORTED_LANGUAGE
        else:
            kind = ErrorKind.NETWORK
        return TranslationResult.failure(kind, message, diagnostic=f"HTTPError:{code}")
    if isinstance(exc, ssl.SSLCertVerificationError) or (
        isinstance(exc, urllib.error.URLError)
        and isinstance(exc.reason, ssl.SSLCertVerificationError)
    ):
        return TranslationResult.failure(
            ErrorKind.TLS,
            _(
                "Could not verify {provider}'s security certificate. "
                "Check the system clock and CA certificates."
            ).format(provider=provider),
            diagnostic="SSLCertVerificationError",
        )
    if isinstance(exc, (TimeoutError, urllib.error.URLError)):
        reason = exc.reason if isinstance(exc, urllib.error.URLError) else exc
        if isinstance(reason, TimeoutError):
            return TranslationResult.failure(
                ErrorKind.TIMEOUT,
                _("{provider} timed out. Please try again.").format(provider=provider),
                diagnostic="TimeoutError",
            )
        return TranslationResult.failure(
            ErrorKind.NETWORK,
            _("Could not connect to {provider}.").format(provider=provider),
            diagnostic=type(reason).__name__,
        )
    if isinstance(exc, (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError)):
        return TranslationResult.failure(
            ErrorKind.MALFORMED_RESPONSE,
            _("{provider} returned an invalid response.").format(provider=provider),
            diagnostic=type(exc).__name__,
        )
    return TranslationResult.failure(
        ErrorKind.UNKNOWN,
        _("{provider} translation failed.").format(provider=provider),
        diagnostic=type(exc).__name__,
    )

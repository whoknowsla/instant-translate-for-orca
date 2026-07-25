# Copyright (C) 2026 the Instant Translate for Orca contributors.
#
# SPDX-License-Identifier: GPL-2.0-only
"""Typed data shared by the extension, coordinator, and translation backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ErrorKind(StrEnum):
    """Stable categories for failures that are safe to expose to the UI."""

    AUTHENTICATION = "authentication"
    CANCELLED = "cancelled"
    INVALID_REQUEST = "invalid-request"
    MALFORMED_RESPONSE = "malformed-response"
    NETWORK = "network"
    QUOTA = "quota"
    RATE_LIMIT = "rate-limit"
    RESPONSE_TOO_LARGE = "response-too-large"
    TIMEOUT = "timeout"
    TLS = "tls"
    UNSUPPORTED_LANGUAGE = "unsupported-language"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class TranslationRequest:
    """A provider-independent translation request."""

    engine: str
    source_language: str
    target_language: str
    text: str
    identify_only: bool = False
    use_mirror: bool = False
    deepl_plan: str = "free"
    deepl_api_key: str = field(default="", repr=False)
    forget_deepl_key: bool = False
    cache_key: tuple[str, str, str, str] | None = None


@dataclass(frozen=True, slots=True)
class TranslationResult:
    """The complete result of one backend operation."""

    translation: str = ""
    detected_language: str = ""
    error_kind: ErrorKind | None = None
    error_message: str | None = None
    diagnostic: str | None = None
    cancelled: bool = False
    credential_warning: str | None = None

    @property
    def ok(self) -> bool:
        return self.error_kind is None and not self.cancelled

    @classmethod
    def failure(
        cls,
        kind: ErrorKind,
        message: str,
        *,
        diagnostic: str | None = None,
    ) -> TranslationResult:
        return cls(error_kind=kind, error_message=message, diagnostic=diagnostic)

    @classmethod
    def cancelled_result(cls) -> TranslationResult:
        return cls(error_kind=ErrorKind.CANCELLED, cancelled=True)

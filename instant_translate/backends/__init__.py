# Copyright (C) 2026 the Instant Translate for Orca contributors.
#
# SPDX-License-Identifier: GPL-2.0-only
"""Synchronous provider implementations used by the bounded coordinator."""

from .deepl import DeepLBackend
from .google import GoogleBackend
from .yandex import YandexBackend

__all__ = ["DeepLBackend", "GoogleBackend", "YandexBackend"]

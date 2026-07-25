# Copyright (C) 2026 the Instant Translate for Orca contributors.
#
# SPDX-License-Identifier: GPL-2.0-only
"""DeepL credential storage backed by the desktop Secret Service."""

from __future__ import annotations

from typing import ClassVar

try:
    import gi

    gi.require_version("Secret", "1")
    from gi.repository import Secret
except (ImportError, ValueError):  # pragma: no cover - depends on host packages
    Secret = None


class SecretStoreError(RuntimeError):
    """Raised without embedding a credential or a Secret Service response."""


class DeepLSecretStore:
    """Stores a single DeepL key in the user's default keyring collection."""

    _ATTRIBUTES: ClassVar[dict[str, str]] = {"account": "deepl-api-key"}

    def __init__(self) -> None:
        self._schema = None
        if Secret is not None:
            self._schema = Secret.Schema.new(
                "org.gnome.Orca.InstantTranslate",
                Secret.SchemaFlags.NONE,
                {"account": Secret.SchemaAttributeType.STRING},
            )

    @property
    def available(self) -> bool:
        return self._schema is not None

    def lookup(self) -> str:
        if self._schema is None:
            return ""
        try:
            return Secret.password_lookup_sync(self._schema, self._ATTRIBUTES, None) or ""
        except Exception as exc:  # GI raises GLib.Error subclasses.
            raise SecretStoreError("Secret Service lookup failed") from exc

    def store(self, api_key: str) -> None:
        if self._schema is None:
            raise SecretStoreError("Secret Service is unavailable")
        try:
            stored = Secret.password_store_sync(
                self._schema,
                self._ATTRIBUTES,
                Secret.COLLECTION_DEFAULT,
                "Instant Translate DeepL API key",
                api_key,
                None,
            )
        except Exception as exc:
            raise SecretStoreError("Secret Service storage failed") from exc
        if not stored:
            raise SecretStoreError("Secret Service storage failed")

    def clear(self) -> None:
        if self._schema is None:
            return
        try:
            Secret.password_clear_sync(self._schema, self._ATTRIBUTES, None)
        except Exception as exc:
            raise SecretStoreError("Secret Service clear failed") from exc

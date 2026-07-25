# Copyright (C) 2026 the Instant Translate for Orca contributors.
#
# This file is covered by the GNU General Public License, version 2.
# See the LICENSE file for details.
#
# SPDX-License-Identifier: GPL-2.0-only
"""Orca integration and translation request orchestration."""

from __future__ import annotations

import logging
import threading
from dataclasses import replace
from typing import Any

import gi

gi.require_version("Atspi", "2.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Atspi, Gdk, GLib, Gtk
from orca import keybindings
from orca.command import Command, KeyboardCommand
from orca.extension import ExtensionPreference

from .backends import DeepLBackend, GoogleBackend, YandexBackend
from .cache import TranslationCache
from .coordinator import LatestRequestCoordinator
from .engines import (
    ENGINE_OPTIONS,
    current_engine,
    get_engine_spec,
    migrate_legacy_language_settings,
    read_languages,
)
from .google_chunking import split_chunks
from .i18n import _
from .models import ErrorKind, TranslationRequest, TranslationResult
from .secret_store import DeepLSecretStore, SecretStoreError

_LOGGER = logging.getLogger(__name__)


class _InstantTranslateImplementation:
    """Implementation mixed into the Orca-visible class declared by the package."""

    # These attributes are supplied by Orca's Extension base class. Keeping the
    # implementation as a mixin lets __init__.py declare the direct Extension
    # subclass required by Orca's non-executing metadata scanner.
    GROUP_LABEL: str
    controller: Any
    settings: Any

    def __init__(self) -> None:
        self._last_translation: str | None = None
        self._shutting_down = False
        self._translation_cache = TranslationCache()
        self._wait_timeout_ids: dict[int, int] = {}
        super().__init__()
        migrate_legacy_language_settings(self.settings)
        self._secret_store = DeepLSecretStore()
        self._coordinator = LatestRequestCoordinator(
            self._execute_translation,
            self._queue_completion,
        )

    # -- declarative settings UI -----------------------------------------

    def get_preferences(self) -> list[ExtensionPreference]:
        spec = current_engine(self.settings)
        preferences = [
            ExtensionPreference.enum(
                "engine",
                _("Translation engine"),
                ENGINE_OPTIONS,
                "google",
            ),
            ExtensionPreference.info(
                _(
                    "After changing the engine, apply the setting and reopen this dialog "
                    "to see its language and provider options."
                )
            ),
            ExtensionPreference.enum(
                spec.from_setting,
                _("Source language"),
                (("auto", _("Auto-detect")), *spec.source_choices),
                "auto",
            ),
            ExtensionPreference.enum(
                spec.to_setting,
                _("Target language"),
                spec.target_choices,
                spec.default_target,
            ),
            ExtensionPreference.enum(
                spec.swap_setting,
                _("Language for auto-swap"),
                spec.target_choices,
                spec.default_target,
            ),
            ExtensionPreference.boolean(
                "copy-to-clipboard",
                _("Copy translation result to clipboard"),
                False,
            ),
            ExtensionPreference.boolean(
                "replace-underscores",
                _("Replace underscores with spaces before translating"),
                False,
            ),
        ]

        if spec.key == "google":
            preferences.extend(
                [
                    ExtensionPreference.info(
                        _(
                            "Google uses an unofficial public endpoint. The mirror is a "
                            "separate third-party service intended mainly for users in China."
                        )
                    ),
                    ExtensionPreference.boolean(
                        "use-mirror",
                        _("Use the Google mirror endpoint"),
                        False,
                    ),
                ]
            )
        elif spec.key == "yandex":
            preferences.append(
                ExtensionPreference.info(
                    _(
                        "Yandex uses an unofficial mobile endpoint that can change or stop "
                        "working without notice."
                    )
                )
            )

        if spec.key in {"yandex", "deepl"}:
            preferences.append(
                ExtensionPreference.integer(
                    "max-input-characters",
                    _("Maximum characters per Yandex or DeepL translation"),
                    20_000,
                    1_000,
                    100_000,
                )
            )

        preferences.append(
            ExtensionPreference.boolean(
                "cache-translations",
                _("Cache translations in memory for this Orca session"),
                False,
            )
        )

        if spec.key == "deepl":
            preferences.extend(
                [
                    ExtensionPreference.info(
                        _(
                            "Enter a DeepL key below. On the next DeepL request it is removed "
                            "from Orca settings and stored in the desktop keyring. Orca cannot "
                            "currently mask generated string fields, so protect the screen "
                            "while entering it."
                        )
                    ),
                    ExtensionPreference.string(
                        "deepl-api-key",
                        _("New or replacement DeepL API key"),
                        "",
                    ),
                    ExtensionPreference.enum(
                        "deepl-plan",
                        _("DeepL plan"),
                        (("free", _("Free")), ("pro", _("Pro"))),
                        "free",
                    ),
                    ExtensionPreference.boolean(
                        "deepl-forget-api-key",
                        _("Forget the stored DeepL key on the next DeepL request"),
                        False,
                    ),
                ]
            )
        return preferences

    # -- commands and keybindings ----------------------------------------

    def _get_commands(self) -> list[Command]:
        mods = keybindings.ORCA_ALT_MODIFIER_MASK

        def binding(key: str) -> keybindings.KeyBinding:
            return keybindings.KeyBinding(key, mods)

        return [
            KeyboardCommand(
                "translate_selection",
                self.translate_selection,
                self.GROUP_LABEL,
                _("Translates the selected text"),
                desktop_keybinding=binding("x"),
                laptop_keybinding=binding("x"),
            ),
            KeyboardCommand(
                "translate_clipboard",
                self.translate_clipboard,
                self.GROUP_LABEL,
                _("Translates the clipboard text"),
                desktop_keybinding=binding("c"),
                laptop_keybinding=binding("c"),
            ),
            KeyboardCommand(
                "swap_languages",
                self.swap_languages,
                self.GROUP_LABEL,
                _("Swaps the source and target languages"),
                desktop_keybinding=binding("s"),
                laptop_keybinding=binding("s"),
            ),
            KeyboardCommand(
                "announce_languages",
                self.announce_languages,
                self.GROUP_LABEL,
                _("Announces the current source and target languages"),
                desktop_keybinding=binding("a"),
                laptop_keybinding=binding("a"),
            ),
            KeyboardCommand(
                "identify_language",
                self.identify_language,
                self.GROUP_LABEL,
                _("Identifies the language of the selected text"),
                desktop_keybinding=binding("i"),
                laptop_keybinding=binding("i"),
            ),
        ]

    # -- AT-SPI / clipboard ----------------------------------------------

    def _get_selected_text(self) -> str | None:
        obj = self.controller.get_current_object_internal()
        if obj is None:
            return None
        try:
            if Atspi.Accessible.get_text_iface(obj) is None:
                return None
            if Atspi.Text.get_n_selections(obj) <= 0:
                return None
            selection = Atspi.Text.get_selection(obj, 0)
            text = Atspi.Text.get_text(obj, selection.start_offset, selection.end_offset)
        except GLib.GError:
            return None
        return text or None

    def _request_clipboard_text(self, callback) -> None:
        clipboard = Gtk.Clipboard.get(Gdk.Atom.intern("CLIPBOARD", False))
        clipboard.request_text(self._on_clipboard_text, callback)

    def _on_clipboard_text(self, _clipboard, text: str | None, callback) -> None:
        if not self._shutting_down:
            callback(text)

    # -- translation pipeline --------------------------------------------

    def _start_translation(self, text: str, *, identify_only: bool = False) -> None:
        if not text or text.isspace():
            message = _("No text to identify.") if identify_only else _("No text to translate.")
            self.controller.present_message_internal(message)
            return
        if self.settings.get("replace-underscores", default=False):
            text = text.replace("_", " ")

        spec = current_engine(self.settings)
        if spec.key != "google":
            maximum = self.settings.get("max-input-characters", default=20_000)
            if len(text) > maximum:
                self.controller.present_message_internal(
                    _(
                        "This text has {count:,} characters; the configured "
                        "{provider} limit is {maximum:,}."
                    ).format(count=len(text), provider=spec.label, maximum=maximum)
                )
                return
        source, target, _swap_target = read_languages(self.settings, spec)
        if identify_only:
            source = "auto"

        cache_enabled = self.settings.get("cache-translations", default=False)
        cache_key = (spec.key, source, target, text)
        cached = (
            self._translation_cache.get(cache_key)
            if cache_enabled and not identify_only
            else None
        )
        if cached is not None:
            self._coordinator.supersede()
            self._remove_wait_timers()
            self._present_translation(cached)
            return

        api_key = ""
        forget_key = False
        if spec.key == "deepl":
            api_key = self.settings.get("deepl-api-key", default="").strip()
            if api_key:
                # Minimize the period during which Orca's ordinary string
                # preference leaves the key in dconf. The background job owns
                # the in-memory copy and migrates it to Secret Service.
                self.settings.reset("deepl-api-key")
            forget_key = self.settings.get("deepl-forget-api-key", default=False)
            if forget_key:
                self.settings.reset("deepl-forget-api-key")

        request = TranslationRequest(
            engine=spec.key,
            source_language=source,
            target_language=target,
            text=text,
            identify_only=identify_only,
            use_mirror=(
                self.settings.get("use-mirror", default=False) if spec.key == "google" else False
            ),
            deepl_plan=self.settings.get("deepl-plan", default="free"),
            deepl_api_key=api_key,
            forget_deepl_key=forget_key,
            cache_key=cache_key if cache_enabled and not identify_only else None,
        )
        try:
            self._remove_wait_timers()
            request_id = self._coordinator.submit(request)
        except RuntimeError:
            return
        self._wait_timeout_ids[request_id] = GLib.timeout_add(
            1000,
            self._on_wait_tick,
            request_id,
        )

    def _execute_translation(
        self,
        request: TranslationRequest,
        cancel_event: threading.Event,
    ) -> TranslationResult:
        if cancel_event.is_set():
            return TranslationResult.cancelled_result()
        if request.engine == "google":
            return GoogleBackend(split_chunks).translate(request, cancel_event)
        if request.engine == "yandex":
            return YandexBackend().translate(request, cancel_event)
        if request.engine != "deepl":
            return TranslationResult.failure(
                ErrorKind.INVALID_REQUEST,
                _("The selected translation engine is not supported."),
            )

        warning = None
        try:
            if request.forget_deepl_key:
                self._secret_store.clear()
            api_key = request.deepl_api_key
            if api_key:
                try:
                    self._secret_store.store(api_key)
                except SecretStoreError:
                    warning = (
                        _(
                            "The DeepL key was used for this request but could not be saved "
                            "in the desktop keyring."
                        )
                    )
            elif not request.forget_deepl_key:
                api_key = self._secret_store.lookup()
        except SecretStoreError as exc:
            return TranslationResult.failure(
                ErrorKind.AUTHENTICATION,
                _("The desktop keyring could not be accessed for the DeepL API key."),
                diagnostic=type(exc).__name__,
            )

        if request.forget_deepl_key and not api_key:
            return TranslationResult.failure(
                ErrorKind.AUTHENTICATION,
                _("The stored DeepL API key was removed."),
            )
        if not api_key:
            return TranslationResult.failure(
                ErrorKind.AUTHENTICATION,
                _("DeepL API key is not set."),
            )

        result = DeepLBackend(api_key, request.deepl_plan).translate(request, cancel_event)
        return replace(result, credential_warning=warning) if warning else result

    def _queue_completion(
        self,
        request_id: int,
        request: TranslationRequest,
        result: TranslationResult,
        is_latest: bool,
    ) -> None:
        GLib.idle_add(self._finish_translation, request_id, request, result, is_latest)

    def _on_wait_tick(self, request_id: int) -> bool:
        if self._shutting_down or request_id not in self._wait_timeout_ids:
            return False
        self.controller.play_tone_internal(0.1, 500)
        return True

    def _finish_translation(
        self,
        request_id: int,
        request: TranslationRequest,
        result: TranslationResult,
        is_latest: bool,
    ) -> bool:
        self._remove_wait_timer(request_id)
        if (
            self._shutting_down
            or not is_latest
            or not self._coordinator.is_latest(request_id)
            or result.cancelled
        ):
            return False
        if result.diagnostic:
            _LOGGER.warning(
                "INSTANT TRANSLATE: %s: %s",
                request.engine,
                result.diagnostic,
            )
        if not result.ok:
            self.controller.play_tone_internal(0.1, 120)
            fallback = (
                _("Language identification failed.")
                if request.identify_only
                else _("Translation failed.")
            )
            self.controller.present_message_internal(result.error_message or fallback)
            return False
        if request.identify_only:
            spec = get_engine_spec(request.engine)
            self.controller.present_message_internal(
                _("Detected language: {language}").format(
                    language=spec.label_for(result.detected_language)
                )
            )
            return False
        if request.cache_key is not None:
            self._translation_cache[request.cache_key] = result.translation
        self._present_translation(result.translation)
        if result.credential_warning:
            self.controller.present_message_internal(result.credential_warning)
        return False

    def _remove_wait_timer(self, request_id: int) -> None:
        timeout_id = self._wait_timeout_ids.pop(request_id, None)
        if timeout_id is not None:
            GLib.source_remove(timeout_id)

    def _remove_wait_timers(self) -> None:
        for request_id in tuple(self._wait_timeout_ids):
            self._remove_wait_timer(request_id)

    def _present_translation(self, translation: str) -> None:
        self._last_translation = translation
        self.controller.present_message_internal(translation)
        if self.settings.get("copy-to-clipboard", default=False):
            self.controller.set_clipboard_text_internal(translation)

    # -- command bodies ---------------------------------------------------

    def translate_selection(self) -> bool:
        text = self._get_selected_text()
        if not text:
            self.controller.present_message_internal(_("No selection."))
            return True
        self._start_translation(text)
        return True

    def translate_clipboard(self) -> bool:
        def translate(text: str | None) -> None:
            if not text or text.isspace():
                self.controller.present_message_internal(
                    _("There is no text on the clipboard.")
                )
                return
            self._start_translation(text)

        self._request_clipboard_text(translate)
        return True

    def identify_language(self) -> bool:
        text = self._get_selected_text()
        if not text:
            self.controller.present_message_internal(_("No selection."))
            return True
        self._start_translation(text, identify_only=True)
        return True

    def swap_languages(self) -> bool:
        spec = current_engine(self.settings)
        source, target, swap_target = read_languages(self.settings, spec)
        new_source, new_target = spec.swap(source, target, swap_target)
        self.settings.set(spec.from_setting, new_source)
        self.settings.set(spec.to_setting, new_target)
        self.controller.present_message_internal(_("Languages swapped."))
        self.announce_languages()
        text = self._get_selected_text()
        if text:
            self._start_translation(text)
        return True

    def announce_languages(self) -> bool:
        spec = current_engine(self.settings)
        source, target, _swap_target = read_languages(self.settings, spec)
        self.controller.present_message_internal(
            _("Translate: from {source} to {target}").format(
                source=spec.label_for(source),
                target=spec.label_for(target),
            )
        )
        return True

    # -- shutdown ---------------------------------------------------------

    def on_shutdown(self) -> None:
        if self._shutting_down:
            return
        self._shutting_down = True
        self._coordinator.close()
        self._remove_wait_timers()

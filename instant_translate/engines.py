# Copyright (C) 2026 the Instant Translate for Orca contributors.
#
# SPDX-License-Identifier: GPL-2.0-only
"""Translation-engine metadata, settings keys, and language normalization."""

from __future__ import annotations

import locale
import os
from dataclasses import dataclass
from typing import Protocol

from . import deepl_langs, langs, yandex_langs
from .i18n import _


class Settings(Protocol):
    def get(self, key: str, default=None): ...

    def set(self, key: str, value) -> bool: ...

    def reset(self, key: str) -> bool: ...


def _google_default_target() -> str:
    lang_tag = locale.getlocale()[0] or os.environ.get("LANG", "en_US").split(".")[0]
    normalized = lang_tag.replace("_", "-")
    if normalized.startswith("zh"):
        candidate = "zh-TW" if normalized in {"zh-HK", "zh-TW"} else "zh-CN"
    else:
        candidate = normalized.split("-", 1)[0]
    return candidate if candidate in langs.LANGUAGES else "en"


@dataclass(frozen=True, slots=True)
class EngineSpec:
    key: str
    label: str
    source_choices: tuple[tuple[str, str], ...]
    target_choices: tuple[tuple[str, str], ...]
    default_target: str

    @property
    def from_setting(self) -> str:
        return f"{self.key}-from-language"

    @property
    def to_setting(self) -> str:
        return f"{self.key}-to-language"

    @property
    def swap_setting(self) -> str:
        return f"{self.key}-swap-language"

    @property
    def source_codes(self) -> frozenset[str]:
        return frozenset(code for code, _label in self.source_choices)

    @property
    def target_codes(self) -> frozenset[str]:
        return frozenset(code for code, _label in self.target_choices)

    def normalize_source(self, code: str) -> str:
        if code == "auto" or code in self.source_codes:
            return code
        return "auto"

    def normalize_target(self, code: str) -> str:
        return code if code in self.target_codes else self.default_target

    def source_from_target(self, code: str) -> str:
        if self.key == "deepl":
            code = {
                "DE-CH": "DE",
                "EN-GB": "EN",
                "EN-US": "EN",
                "ES-419": "ES",
                "FR-CA": "FR",
                "PT-BR": "PT",
                "PT-PT": "PT",
                "ZH-HANS": "ZH",
                "ZH-HANT": "ZH",
            }.get(code, code)
        return code if code in self.source_codes else "auto"

    def target_from_source(self, code: str) -> str:
        if self.key == "deepl":
            code = {"EN": "EN-US", "PT": "PT-PT"}.get(code, code)
        return self.normalize_target(code)

    def label_for(self, code: str) -> str:
        if self.key == "yandex":
            return yandex_langs.language_label(code)
        if self.key == "deepl":
            return deepl_langs.language_label(code)
        return langs.language_label(code)

    def swap(self, source: str, target: str, auto_swap_target: str) -> tuple[str, str]:
        source = self.normalize_source(source)
        target = self.normalize_target(target)
        if source == "auto":
            return self.source_from_target(target), self.normalize_target(auto_swap_target)
        return self.source_from_target(target), self.target_from_source(source)


def _build_specs() -> dict[str, EngineSpec]:
    return {
        "google": EngineSpec(
            "google",
            _("Google Translate (unofficial)"),
            langs.language_choices(),
            langs.language_choices(),
            _google_default_target(),
        ),
        "yandex": EngineSpec(
            "yandex",
            _("Yandex Translate (unofficial)"),
            yandex_langs.language_choices(),
            yandex_langs.language_choices(),
            yandex_langs.DEFAULT_TARGET,
        ),
        "deepl": EngineSpec(
            "deepl",
            _("DeepL API"),
            deepl_langs.source_language_choices(),
            deepl_langs.target_language_choices(),
            deepl_langs.DEFAULT_TARGET,
        ),
    }


ENGINE_SPECS = _build_specs()
ENGINE_OPTIONS = tuple((key, spec.label) for key, spec in ENGINE_SPECS.items())


def get_engine_spec(engine: str) -> EngineSpec:
    return ENGINE_SPECS.get(engine, ENGINE_SPECS["google"])


def current_engine(settings: Settings) -> EngineSpec:
    return get_engine_spec(settings.get("engine", default="google"))


def read_languages(settings: Settings, spec: EngineSpec) -> tuple[str, str, str]:
    source = spec.normalize_source(settings.get(spec.from_setting, default="auto"))
    target = spec.normalize_target(settings.get(spec.to_setting, default=spec.default_target))
    swap_target = spec.normalize_target(
        settings.get(spec.swap_setting, default=spec.default_target)
    )
    return source, target, swap_target


def migrate_legacy_language_settings(settings: Settings) -> None:
    """Move the original shared language keys to the active engine once."""

    if settings.get("settings-version", default=0) >= 1:
        return
    spec = current_engine(settings)
    legacy = (
        ("from-language", spec.from_setting, spec.normalize_source, "auto"),
        ("to-language", spec.to_setting, spec.normalize_target, spec.default_target),
        ("swap-language", spec.swap_setting, spec.normalize_target, spec.default_target),
    )
    for old_key, new_key, normalize, missing in legacy:
        value = settings.get(old_key, default=missing)
        settings.set(new_key, normalize(value))
        settings.reset(old_key)
    settings.set("settings-version", 1)

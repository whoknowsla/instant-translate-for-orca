# Copyright (C) 2026 the Instant Translate for Orca contributors.
#
# SPDX-License-Identifier: GPL-2.0-only
"""gettext helpers for extension-owned user-interface strings."""

from __future__ import annotations

import gettext
from pathlib import Path

try:
    from orca.extension import get_translation as _orca_get_translation
except ImportError:  # Orca releases from before extension localization support.
    _orca_get_translation = None


def _load_translation() -> gettext.NullTranslations:
    if _orca_get_translation is not None:
        return _orca_get_translation(__file__)

    package_dir = Path(__file__).resolve().parent
    return gettext.translation(
        package_dir.name,
        localedir=package_dir / "locale",
        fallback=True,
    )


_translation = _load_translation()
_ = _translation.gettext
ngettext = _translation.ngettext
pgettext = _translation.pgettext
npgettext = _translation.npgettext


def N_(message: str) -> str:
    """Mark a deferred string for catalog extraction without translating it yet."""

    return message


__all__ = ["N_", "_", "ngettext", "npgettext", "pgettext"]

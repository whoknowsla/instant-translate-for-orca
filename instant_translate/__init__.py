# Copyright (C) 2026 the Instant Translate for Orca contributors.
#
# This file is covered by the GNU General Public License, version 2.
# See the LICENSE file for details.
#
# SPDX-License-Identifier: GPL-2.0-only
"""Instant Translate for Orca."""

from __future__ import annotations

import sys
import types

from orca.extension import Extension

from .i18n import _

# Orca 51.alpha loads user-extension packages under names such as
# ``orca_user_extension.instant_translate`` without first creating the parent
# namespace. Keep the loader workaround isolated from the extension itself.
if __package__ and __package__.startswith("orca_user_extension."):
    namespace = __package__.partition(".")[0]
    if namespace not in sys.modules:
        namespace_module = types.ModuleType(namespace)
        namespace_module.__path__ = []
        namespace_module.__package__ = namespace
        sys.modules[namespace] = namespace_module

from .extension import _InstantTranslateImplementation


class InstantTranslate(_InstantTranslateImplementation, Extension):
    """Translates selected or clipboard text through the configured provider."""

    # Orca reads these constants from this file's AST without importing the
    # package. The Extension base and metadata must therefore remain declared
    # directly here even though the implementation lives in extension.py.
    GROUP_LABEL = "Instant Translate"
    DESCRIPTION = (
        "Translates selected or clipboard text using Google Translate, "
        "Yandex Translate, or DeepL."
    )
    VERSION = "1.0"
    AUTHOR = "Deniz Aygun"
    ORGANIZATION = ""
    COPYRIGHT = ""
    WEBSITE = "https://github.com/whoknowsla/instant-translate-for-orca"


# Keep literal metadata above for older Orca versions whose safe, non-executing
# scanner only understands constants. Approved instances use localized values.
InstantTranslate.GROUP_LABEL = _("Instant Translate")
InstantTranslate.DESCRIPTION = _(
    "Translates selected or clipboard text using Google Translate, "
    "Yandex Translate, or DeepL."
)

__all__ = ["InstantTranslate"]

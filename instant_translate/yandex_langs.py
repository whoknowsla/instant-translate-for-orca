# Copyright (C) 2026 the Instant Translate for Orca contributors.
# Language codes ported from YandexTranslate for NVDA's languages.py by
# alekssamos (https://github.com/alekssamos/YandexTranslate), MIT licensed.
#
# This file is covered by the GNU General Public License, version 2.
# See the LICENSE file for details.
#
# SPDX-License-Identifier: GPL-2.0-only
"""Language code to display-name table for Yandex Translate's unofficial API."""

from __future__ import annotations

from .i18n import N_, _

LANGUAGES: dict[str, str] = {
    "af": N_("Afrikaans"),
    "am": N_("Amharic"),
    "ar": N_("Arabic"),
    "az": N_("Azerbaijani"),
    "ba": N_("Bashkir"),
    "be": N_("Belarusian"),
    "bg": N_("Bulgarian"),
    "bn": N_("Bengali"),
    "bs": N_("Bosnian"),
    "ca": N_("Catalan"),
    "ceb": N_("Cebuano"),
    "cs": N_("Czech"),
    "cv": N_("Chuvash"),
    "cy": N_("Welsh"),
    "da": N_("Danish"),
    "de": N_("German"),
    "el": N_("Greek"),
    "en": N_("English"),
    "eo": N_("Esperanto"),
    "es": N_("Spanish"),
    "et": N_("Estonian"),
    "eu": N_("Basque"),
    "fa": N_("Persian"),
    "fi": N_("Finnish"),
    "fr": N_("French"),
    "ga": N_("Irish"),
    "gd": N_("Scottish Gaelic"),
    "gl": N_("Galician"),
    "gu": N_("Gujarati"),
    "he": N_("Hebrew"),
    "hi": N_("Hindi"),
    "hr": N_("Croatian"),
    "ht": N_("Haitian"),
    "hu": N_("Hungarian"),
    "hy": N_("Armenian"),
    "id": N_("Indonesian"),
    "is": N_("Icelandic"),
    "it": N_("Italian"),
    "ja": N_("Japanese"),
    "jv": N_("Javanese"),
    "ka": N_("Georgian"),
    "kk": N_("Kazakh"),
    "km": N_("Khmer"),
    "kn": N_("Kannada"),
    "ko": N_("Korean"),
    "ky": N_("Kyrgyz"),
    "la": N_("Latin"),
    "lb": N_("Luxembourgish"),
    "lo": N_("Lao"),
    "lt": N_("Lithuanian"),
    "lv": N_("Latvian"),
    "mg": N_("Malagasy"),
    "mhr": N_("Mari"),
    "mi": N_("Maori"),
    "mk": N_("Macedonian"),
    "ml": N_("Malayalam"),
    "mn": N_("Mongolian"),
    "mr": N_("Marathi"),
    "mrj": N_("Hill Mari"),
    "ms": N_("Malay"),
    "mt": N_("Maltese"),
    "my": N_("Burmese"),
    "ne": N_("Nepali"),
    "nl": N_("Dutch"),
    "no": N_("Norwegian"),
    "pa": N_("Punjabi"),
    "pap": N_("Papiamento"),
    "pl": N_("Polish"),
    "pt": N_("Portuguese"),
    "ro": N_("Romanian"),
    "ru": N_("Russian"),
    "si": N_("Sinhalese"),
    "sk": N_("Slovak"),
    "sl": N_("Slovenian"),
    "sq": N_("Albanian"),
    "sr": N_("Serbian"),
    "su": N_("Sundanese"),
    "sv": N_("Swedish"),
    "sw": N_("Swahili"),
    "ta": N_("Tamil"),
    "te": N_("Telugu"),
    "tg": N_("Tajik"),
    "th": N_("Thai"),
    "tl": N_("Tagalog"),
    "tr": N_("Turkish"),
    "tt": N_("Tatar"),
    "udm": N_("Udmurt"),
    "uk": N_("Ukrainian"),
    "ur": N_("Urdu"),
    "uz": N_("Uzbek"),
    "vi": N_("Vietnamese"),
    "xh": N_("Xhosa"),
    "yi": N_("Yiddish"),
    "zh": N_("Chinese"),
}

DEFAULT_TARGET = "en"


def language_label(code: str) -> str:
    """Returns a human-readable label for a Yandex language code."""

    if code == "auto":
        return _("Auto-detect")
    label = LANGUAGES.get(code)
    return _(label) if label is not None else code


def language_choices() -> tuple[tuple[str, str], ...]:
    """Returns (code, label) pairs sorted by label, for enum preferences."""

    return tuple(
        sorted(
            ((code, _(label)) for code, label in LANGUAGES.items()),
            key=lambda pair: pair[1],
        )
    )

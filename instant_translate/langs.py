# Copyright (C) 2026 the Instant Translate for Orca contributors.
#
# This file is covered by the GNU General Public License, version 2.
# See the LICENSE file for details.
#
# SPDX-License-Identifier: GPL-2.0-only
"""Language code to display-name table used for the translation settings UI
and for announcing source/target/detected languages.

This is a plain data table (no Orca- or NVDA-specific logic), roughly
matching the set of languages Google Translate supports.
"""

from __future__ import annotations

from .i18n import N_, _

LANGUAGES: dict[str, str] = {
    "af": N_("Afrikaans"),
    "sq": N_("Albanian"),
    "am": N_("Amharic"),
    "ar": N_("Arabic"),
    "hy": N_("Armenian"),
    "az": N_("Azerbaijani"),
    "eu": N_("Basque"),
    "be": N_("Belarusian"),
    "bn": N_("Bengali"),
    "bs": N_("Bosnian"),
    "bg": N_("Bulgarian"),
    "ca": N_("Catalan"),
    "ceb": N_("Cebuano"),
    "ny": N_("Chichewa"),
    "zh-CN": N_("Chinese (Simplified)"),
    "zh-TW": N_("Chinese (Traditional)"),
    "co": N_("Corsican"),
    "hr": N_("Croatian"),
    "cs": N_("Czech"),
    "da": N_("Danish"),
    "nl": N_("Dutch"),
    "en": N_("English"),
    "eo": N_("Esperanto"),
    "et": N_("Estonian"),
    "tl": N_("Filipino"),
    "fi": N_("Finnish"),
    "fr": N_("French"),
    "fy": N_("Frisian"),
    "gl": N_("Galician"),
    "ka": N_("Georgian"),
    "de": N_("German"),
    "el": N_("Greek"),
    "gu": N_("Gujarati"),
    "ht": N_("Haitian Creole"),
    "ha": N_("Hausa"),
    "haw": N_("Hawaiian"),
    "he": N_("Hebrew"),
    "hi": N_("Hindi"),
    "hmn": N_("Hmong"),
    "hu": N_("Hungarian"),
    "is": N_("Icelandic"),
    "ig": N_("Igbo"),
    "id": N_("Indonesian"),
    "ga": N_("Irish"),
    "it": N_("Italian"),
    "ja": N_("Japanese"),
    "jv": N_("Javanese"),
    "kn": N_("Kannada"),
    "kk": N_("Kazakh"),
    "km": N_("Khmer"),
    "rw": N_("Kinyarwanda"),
    "ko": N_("Korean"),
    "ku": N_("Kurdish"),
    "ky": N_("Kyrgyz"),
    "lo": N_("Lao"),
    "la": N_("Latin"),
    "lv": N_("Latvian"),
    "lt": N_("Lithuanian"),
    "lb": N_("Luxembourgish"),
    "mk": N_("Macedonian"),
    "mg": N_("Malagasy"),
    "ms": N_("Malay"),
    "ml": N_("Malayalam"),
    "mt": N_("Maltese"),
    "mi": N_("Maori"),
    "mr": N_("Marathi"),
    "mn": N_("Mongolian"),
    "my": N_("Myanmar (Burmese)"),
    "ne": N_("Nepali"),
    "no": N_("Norwegian"),
    "or": N_("Odia"),
    "ps": N_("Pashto"),
    "fa": N_("Persian"),
    "pl": N_("Polish"),
    "pt": N_("Portuguese"),
    "pa": N_("Punjabi"),
    "ro": N_("Romanian"),
    "ru": N_("Russian"),
    "sm": N_("Samoan"),
    "gd": N_("Scots Gaelic"),
    "sr": N_("Serbian"),
    "st": N_("Sesotho"),
    "sn": N_("Shona"),
    "sd": N_("Sindhi"),
    "si": N_("Sinhala"),
    "sk": N_("Slovak"),
    "sl": N_("Slovenian"),
    "so": N_("Somali"),
    "es": N_("Spanish"),
    "su": N_("Sundanese"),
    "sw": N_("Swahili"),
    "sv": N_("Swedish"),
    "tg": N_("Tajik"),
    "ta": N_("Tamil"),
    "tt": N_("Tatar"),
    "te": N_("Telugu"),
    "th": N_("Thai"),
    "tr": N_("Turkish"),
    "tk": N_("Turkmen"),
    "uk": N_("Ukrainian"),
    "ur": N_("Urdu"),
    "ug": N_("Uyghur"),
    "uz": N_("Uzbek"),
    "vi": N_("Vietnamese"),
    "cy": N_("Welsh"),
    "xh": N_("Xhosa"),
    "yi": N_("Yiddish"),
    "yo": N_("Yoruba"),
    "zu": N_("Zulu"),
}


def language_label(code: str) -> str:
    """Returns a human-readable label for a language code.

    Returns "Auto-detect" for "auto" and the code itself, uppercased for
    readability, if it isn't in the table (e.g. a code Google returns that
    this table doesn't happen to list).
    """

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

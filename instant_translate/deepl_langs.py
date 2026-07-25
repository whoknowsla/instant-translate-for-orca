# Copyright (C) 2026 the Instant Translate for Orca contributors.
#
# This file is covered by the GNU General Public License, version 2.
# See the LICENSE file for details.
#
# SPDX-License-Identifier: GPL-2.0-only
"""Language code tables for the DeepL text-translation API.

Snapshot date: 2026-07-19.
Source: https://developers.deepl.com/docs/getting-started/supported-languages

DeepL uses upper-case codes. Entries marked as variants in the official
catalog are target-only, while English and Portuguese retain asymmetric base
source codes and regional target codes.
"""

from __future__ import annotations

from .i18n import N_, _

# Non-variant languages accepted as sources by DeepL text translation.
SOURCE_LANGUAGES: dict[str, str] = {
    "ACE": N_("Acehnese"),
    "AF": N_("Afrikaans"),
    "AN": N_("Aragonese"),
    "AR": N_("Arabic"),
    "AS": N_("Assamese"),
    "AY": N_("Aymara"),
    "AZ": N_("Azerbaijani"),
    "BA": N_("Bashkir"),
    "BE": N_("Belarusian"),
    "BG": N_("Bulgarian"),
    "BHO": N_("Bhojpuri"),
    "BN": N_("Bengali"),
    "BR": N_("Breton"),
    "BS": N_("Bosnian"),
    "CA": N_("Catalan"),
    "CEB": N_("Cebuano"),
    "CKB": N_("Kurdish (Sorani)"),
    "CS": N_("Czech"),
    "CY": N_("Welsh"),
    "DA": N_("Danish"),
    "DE": N_("German"),
    "EL": N_("Greek"),
    "EN": N_("English"),
    "EO": N_("Esperanto"),
    "ES": N_("Spanish"),
    "ET": N_("Estonian"),
    "EU": N_("Basque"),
    "FA": N_("Persian"),
    "FI": N_("Finnish"),
    "FR": N_("French"),
    "GA": N_("Irish"),
    "GL": N_("Galician"),
    "GN": N_("Guarani"),
    "GOM": N_("Konkani"),
    "GU": N_("Gujarati"),
    "HA": N_("Hausa"),
    "HE": N_("Hebrew"),
    "HI": N_("Hindi"),
    "HR": N_("Croatian"),
    "HT": N_("Haitian Creole"),
    "HU": N_("Hungarian"),
    "HY": N_("Armenian"),
    "ID": N_("Indonesian"),
    "IG": N_("Igbo"),
    "IS": N_("Icelandic"),
    "IT": N_("Italian"),
    "JA": N_("Japanese"),
    "JV": N_("Javanese"),
    "KA": N_("Georgian"),
    "KK": N_("Kazakh"),
    "KMR": N_("Kurdish (Kurmanji)"),
    "KO": N_("Korean"),
    "KY": N_("Kyrgyz"),
    "LA": N_("Latin"),
    "LB": N_("Luxembourgish"),
    "LMO": N_("Lombard"),
    "LN": N_("Lingala"),
    "LT": N_("Lithuanian"),
    "LV": N_("Latvian"),
    "MAI": N_("Maithili"),
    "MG": N_("Malagasy"),
    "MI": N_("Maori"),
    "MK": N_("Macedonian"),
    "ML": N_("Malayalam"),
    "MN": N_("Mongolian"),
    "MR": N_("Marathi"),
    "MS": N_("Malay"),
    "MT": N_("Maltese"),
    "MY": N_("Burmese"),
    "NB": N_("Norwegian Bokmål"),
    "NE": N_("Nepali"),
    "NL": N_("Dutch"),
    "OC": N_("Occitan"),
    "OM": N_("Oromo"),
    "PA": N_("Punjabi"),
    "PAG": N_("Pangasinan"),
    "PAM": N_("Kapampangan"),
    "PL": N_("Polish"),
    "PRS": N_("Dari"),
    "PS": N_("Pashto"),
    "PT": N_("Portuguese"),
    "QU": N_("Quechua"),
    "RO": N_("Romanian"),
    "RU": N_("Russian"),
    "SA": N_("Sanskrit"),
    "SCN": N_("Sicilian"),
    "SK": N_("Slovak"),
    "SL": N_("Slovenian"),
    "SQ": N_("Albanian"),
    "SR": N_("Serbian"),
    "ST": N_("Sesotho"),
    "SU": N_("Sundanese"),
    "SV": N_("Swedish"),
    "SW": N_("Swahili"),
    "TA": N_("Tamil"),
    "TE": N_("Telugu"),
    "TG": N_("Tajik"),
    "TH": N_("Thai"),
    "TK": N_("Turkmen"),
    "TL": N_("Tagalog"),
    "TN": N_("Tswana"),
    "TR": N_("Turkish"),
    "TS": N_("Tsonga"),
    "TT": N_("Tatar"),
    "UK": N_("Ukrainian"),
    "UR": N_("Urdu"),
    "UZ": N_("Uzbek"),
    "VI": N_("Vietnamese"),
    "WO": N_("Wolof"),
    "XH": N_("Xhosa"),
    "YI": N_("Yiddish"),
    "YUE": N_("Cantonese"),
    "ZH": N_("Chinese"),
    "ZU": N_("Zulu"),
}

# Target-only variants from the official catalog.
TARGET_VARIANTS: dict[str, str] = {
    "DE-CH": N_("German (Swiss)"),
    "EN-GB": N_("English (British)"),
    "EN-US": N_("English (American)"),
    "ES-419": N_("Spanish (Latin American)"),
    "FR-CA": N_("French (Canadian)"),
    "PT-BR": N_("Portuguese (Brazilian)"),
    "PT-PT": N_("Portuguese (European)"),
    "ZH-HANS": N_("Chinese (Simplified)"),
    "ZH-HANT": N_("Chinese (Traditional)"),
}

# Bare EN/PT are source roles; DeepL requires a regional target variant.
TARGET_LANGUAGES: dict[str, str] = {
    **{code: label for code, label in SOURCE_LANGUAGES.items() if code not in {"EN", "PT"}},
    **TARGET_VARIANTS,
}

DEFAULT_TARGET = "EN-US"


def language_label(code: str) -> str:
    """Return a human-readable label for a DeepL language code."""

    if code == "auto":
        return _("Auto-detect")
    label = TARGET_LANGUAGES.get(code, SOURCE_LANGUAGES.get(code))
    return _(label) if label is not None else code


def source_language_choices() -> tuple[tuple[str, str], ...]:
    """Return source-language preference choices sorted by label."""

    return tuple(
        sorted(
            ((code, _(label)) for code, label in SOURCE_LANGUAGES.items()),
            key=lambda pair: pair[1],
        )
    )


def target_language_choices() -> tuple[tuple[str, str], ...]:
    """Return target-language preference choices sorted by label."""

    return tuple(
        sorted(
            ((code, _(label)) for code, label in TARGET_LANGUAGES.items()),
            key=lambda pair: pair[1],
        )
    )

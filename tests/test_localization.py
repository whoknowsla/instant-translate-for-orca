# ruff: noqa: RUF001 -- Turkish translations intentionally use dotless i.

import gettext
import pathlib


def _turkish_translation() -> gettext.GNUTranslations:
    package_dir = pathlib.Path(__file__).parents[1] / "instant_translate"
    return gettext.translation(
        "instant_translate",
        localedir=package_dir / "locale",
        languages=["tr"],
    )


def test_turkish_catalog_translates_core_interface_strings():
    translation = _turkish_translation()

    assert translation.gettext("Instant Translate") == "Anında Çeviri"
    assert translation.gettext("Translation engine") == "Çeviri motoru"
    assert translation.gettext("Auto-detect") == "Otomatik algıla"
    assert translation.gettext("Translation failed.") == "Çeviri başarısız oldu."


def test_turkish_catalog_preserves_message_placeholders():
    translated = _turkish_translation().gettext(
        "Translate: from {source} to {target}"
    )

    assert translated.format(source="Türkçe", target="İngilizce") == (
        "Çeviri: Türkçe dilinden İngilizce diline"
    )

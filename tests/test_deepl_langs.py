from instant_translate import deepl_langs


def test_language_label_auto():
    assert deepl_langs.language_label("auto") == "Auto-detect"


def test_language_label_source_code():
    assert deepl_langs.language_label("DE") == "German"


def test_language_label_target_only_variant():
    assert deepl_langs.language_label("EN-US") == "English (American)"


def test_language_label_unknown_code_returns_code():
    assert deepl_langs.language_label("ZZ") == "ZZ"


def test_source_choices_sorted_by_label_no_auto():
    choices = deepl_langs.source_language_choices()
    labels = [label for _, label in choices]
    assert labels == sorted(labels)
    assert "auto" not in [code for code, _ in choices]


def test_target_choices_include_regional_variants():
    codes = [code for code, _ in deepl_langs.target_language_choices()]
    assert "EN-US" in codes
    assert "EN-GB" in codes
    assert "PT-BR" in codes
    assert "PT-PT" in codes
    assert "DE-CH" in codes
    assert "FR-CA" in codes
    assert "ZH-HANS" in codes


def test_target_choices_exclude_bare_variant_base_codes():
    # EN/PT are source-only; DeepL requires a region for these as targets.
    codes = [code for code, _ in deepl_langs.target_language_choices()]
    assert "EN" not in codes
    assert "PT" not in codes


def test_default_target_is_a_valid_target_choice():
    codes = [code for code, _ in deepl_langs.target_language_choices()]
    assert deepl_langs.DEFAULT_TARGET in codes


def test_snapshot_contains_current_extended_catalog():
    assert len(deepl_langs.SOURCE_LANGUAGES) == 114
    assert len(deepl_langs.TARGET_VARIANTS) == 9
    for code in ("ACE", "AF", "BHO", "KMR", "YUE", "ZU"):
        assert code in deepl_langs.SOURCE_LANGUAGES


def test_target_only_variants_are_not_sources():
    assert deepl_langs.TARGET_VARIANTS.keys().isdisjoint(deepl_langs.SOURCE_LANGUAGES)

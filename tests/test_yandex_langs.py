from instant_translate import yandex_langs


def test_language_label_auto():
    assert yandex_langs.language_label("auto") == "Auto-detect"


def test_language_label_known_code():
    assert yandex_langs.language_label("ru") == "Russian"


def test_language_label_unknown_code_returns_code():
    assert yandex_langs.language_label("zz") == "zz"


def test_language_choices_sorted_by_label():
    choices = yandex_langs.language_choices()
    labels = [label for _, label in choices]
    assert labels == sorted(labels)


def test_language_choices_have_no_auto_entry():
    codes = [code for code, _ in yandex_langs.language_choices()]
    assert "auto" not in codes


def test_default_target_is_a_valid_choice():
    codes = [code for code, _ in yandex_langs.language_choices()]
    assert yandex_langs.DEFAULT_TARGET in codes

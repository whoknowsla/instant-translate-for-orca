from instant_translate.engines import (
    ENGINE_SPECS,
    get_engine_spec,
    migrate_legacy_language_settings,
)


class _Settings:
    def __init__(self, values):
        self.values = dict(values)

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value):
        self.values[key] = value
        return True

    def reset(self, key):
        self.values.pop(key, None)
        return True


def test_every_engine_default_is_a_valid_target():
    for spec in ENGINE_SPECS.values():
        assert spec.default_target in spec.target_codes


def test_deepl_swap_normalizes_english_and_portuguese_variants():
    spec = get_engine_spec("deepl")
    assert spec.swap("DE", "EN-GB", "PT-BR") == ("EN", "DE")
    assert spec.swap("EN", "DE", "PT-BR") == ("DE", "EN-US")
    assert spec.swap("PT", "DE", "EN-US") == ("DE", "PT-PT")
    assert spec.swap("EN", "ZH-HANT", "DE") == ("ZH", "EN-US")
    assert spec.swap("FR", "DE-CH", "EN-US") == ("DE", "FR")


def test_unknown_engine_falls_back_to_google():
    assert get_engine_spec("missing").key == "google"


def test_engine_specific_labels_cover_provider_only_codes():
    assert get_engine_spec("yandex").label_for("ba") == "Bashkir"
    assert get_engine_spec("deepl").label_for("EN-US") == "English (American)"


def test_legacy_shared_languages_are_migrated_to_active_engine_once():
    settings = _Settings(
        {
            "engine": "yandex",
            "from-language": "tr",
            "to-language": "en",
            "swap-language": "ru",
        }
    )
    migrate_legacy_language_settings(settings)

    assert settings.values["yandex-from-language"] == "tr"
    assert settings.values["yandex-to-language"] == "en"
    assert settings.values["yandex-swap-language"] == "ru"
    assert "from-language" not in settings.values
    assert settings.values["settings-version"] == 1

    settings.values["yandex-to-language"] = "de"
    migrate_legacy_language_settings(settings)
    assert settings.values["yandex-to-language"] == "de"

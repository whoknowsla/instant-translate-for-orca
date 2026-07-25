import orca.script_manager  # noqa: F401 -- resolves a circular import in orca.extension
import pytest
from conftest import clear_extension_settings
from orca.extension import ExtensionPreferenceKind

from instant_translate import InstantTranslate


class _PreferencesTestExtension(InstantTranslate):
    """Distinct class name so tests never touch the real deployed extension's
    dconf namespace (extensions/instanttranslate/settings)."""


@pytest.fixture
def extension():
    ext = _PreferencesTestExtension()
    try:
        yield ext
    finally:
        ext.on_shutdown()
        clear_extension_settings(ext)


def _pref(ext, key):
    return next(p for p in ext.get_preferences() if p.key == key)


def _preference_keys(ext):
    return {pref.key for pref in ext.get_preferences()}


def test_engine_preference_defaults_to_google(extension):
    pref = _pref(extension, "engine")
    assert pref.kind == ExtensionPreferenceKind.ENUM
    assert pref.default == "google"
    assert set(code for code, _ in pref.options) == {"google", "yandex", "deepl"}


def test_google_engine_uses_google_language_list(extension):
    pref = _pref(extension, "google-to-language")
    codes = [code for code, _ in pref.options]
    assert "zh-CN" in codes  # Google-specific code


def test_yandex_engine_uses_yandex_language_list(extension):
    extension.settings.set("engine", "yandex")
    pref = _pref(extension, "yandex-to-language")
    codes = [code for code, _ in pref.options]
    assert "zh-CN" not in codes
    assert "zh" in codes


def test_deepl_engine_uses_deepl_language_lists(extension):
    extension.settings.set("engine", "deepl")
    from_pref = _pref(extension, "deepl-from-language")
    to_pref = _pref(extension, "deepl-to-language")
    from_codes = [code for code, _ in from_pref.options]
    to_codes = [code for code, _ in to_pref.options]
    assert "auto" in from_codes
    assert "DE" in from_codes
    assert "EN-US" in to_codes
    assert "DE" not in to_codes or "EN" not in to_codes  # EN is target-only-variant, not bare


def test_switching_engine_preserves_each_engines_language(extension):
    extension.settings.set("google-to-language", "zh-CN")
    extension.settings.set("yandex-to-language", "ru")
    extension.settings.set("engine", "yandex")

    pref = _pref(extension, "yandex-to-language")

    assert pref.default == "en"
    assert extension.settings.get("google-to-language") == "zh-CN"
    assert extension.settings.get("yandex-to-language") == "ru"


def test_get_preferences_has_no_settings_side_effects(extension):
    before = extension.settings._get_local_settings()
    extension.get_preferences()
    assert extension.settings._get_local_settings() == before


def test_deepl_preferences_present(extension):
    extension.settings.set("engine", "deepl")
    key_pref = _pref(extension, "deepl-api-key")
    plan_pref = _pref(extension, "deepl-plan")
    assert key_pref.kind == ExtensionPreferenceKind.STRING
    assert key_pref.default == ""
    assert plan_pref.kind == ExtensionPreferenceKind.ENUM
    assert plan_pref.default == "free"
    assert set(code for code, _ in plan_pref.options) == {"free", "pro"}
    assert "deepl-forget-api-key" in _preference_keys(extension)


def test_google_only_shows_google_engine_preference(extension):
    keys = _preference_keys(extension)

    assert "use-mirror" in keys
    assert "deepl-api-key" not in keys
    assert "deepl-plan" not in keys


def test_yandex_hides_engine_specific_preferences(extension):
    extension.settings.set("engine", "yandex")
    keys = _preference_keys(extension)

    assert "use-mirror" not in keys
    assert "deepl-api-key" not in keys
    assert "deepl-plan" not in keys
    assert "max-input-characters" in keys


def test_deepl_only_shows_deepl_engine_preferences(extension):
    extension.settings.set("engine", "deepl")
    keys = _preference_keys(extension)

    assert "use-mirror" not in keys
    assert "deepl-api-key" in keys
    assert "deepl-plan" in keys
    assert "max-input-characters" in keys


def test_google_does_not_have_an_input_request_limit_preference(extension):
    assert "max-input-characters" not in _preference_keys(extension)


def test_copy_to_clipboard_defaults_off(extension):
    assert _pref(extension, "copy-to-clipboard").default is False


def test_language_preferences_are_scoped_to_active_engine(extension):
    assert "google-from-language" in _preference_keys(extension)
    extension.settings.set("engine", "deepl")
    keys = _preference_keys(extension)
    assert "deepl-from-language" in keys
    assert "google-from-language" not in keys


def test_cache_translations_preference_present(extension):
    pref = _pref(extension, "cache-translations")
    assert pref.kind == ExtensionPreferenceKind.BOOLEAN
    assert pref.default is False

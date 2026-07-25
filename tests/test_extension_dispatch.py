import threading

import orca.script_manager  # noqa: F401
import pytest
from conftest import clear_extension_settings

from instant_translate import InstantTranslate
from instant_translate.models import ErrorKind, TranslationRequest, TranslationResult


class _DispatchTestExtension(InstantTranslate):
    """Distinct class name so tests use an isolated Orca settings namespace."""


class _FakeCoordinator:
    def __init__(self):
        self.requests = []
        self.superseded = 0
        self.closed = False
        self.latest_id = 0

    def submit(self, request):
        self.requests.append(request)
        self.latest_id += 1
        return self.latest_id

    def supersede(self):
        self.superseded += 1
        self.latest_id += 1

    def is_latest(self, request_id):
        return self.latest_id == 0 or request_id == self.latest_id

    def close(self):
        self.closed = True


class _FakeSecretStore:
    def __init__(self, key=""):
        self.key = key
        self.stored = []
        self.cleared = 0

    def lookup(self):
        return self.key

    def store(self, key):
        self.key = key
        self.stored.append(key)

    def clear(self):
        self.key = ""
        self.cleared += 1


@pytest.fixture
def extension(monkeypatch):
    removed_sources = []
    monkeypatch.setattr(
        "instant_translate.extension.GLib.timeout_add",
        lambda *_args: len(removed_sources) + 100,
    )
    monkeypatch.setattr(
        "instant_translate.extension.GLib.source_remove",
        removed_sources.append,
    )
    ext = _DispatchTestExtension()
    ext._coordinator.close()
    ext._coordinator = _FakeCoordinator()
    ext._secret_store = _FakeSecretStore()
    try:
        yield ext
    finally:
        ext.on_shutdown()
        clear_extension_settings(ext)


def _request(**overrides):
    values = {
        "engine": "google",
        "source_language": "auto",
        "target_language": "en",
        "text": "hello",
    }
    values.update(overrides)
    return TranslationRequest(**values)


def test_google_start_builds_typed_request(extension):
    extension.settings.set("engine", "google")
    extension.settings.set("google-to-language", "tr")
    extension._start_translation("hello")

    request = extension._coordinator.requests[-1]
    assert request.engine == "google"
    assert request.source_language == "auto"
    assert request.target_language == "tr"
    assert request.text == "hello"


def test_yandex_start_uses_engine_scoped_languages(extension):
    extension.settings.set("engine", "yandex")
    extension.settings.set("google-to-language", "zh-CN")
    extension.settings.set("yandex-from-language", "tr")
    extension.settings.set("yandex-to-language", "en")
    extension._start_translation("merhaba")

    request = extension._coordinator.requests[-1]
    assert (request.engine, request.source_language, request.target_language) == (
        "yandex",
        "tr",
        "en",
    )


def test_yandex_and_deepl_input_limit_is_configurable(extension, monkeypatch):
    extension.settings.set("engine", "deepl")
    extension.settings.set("max-input-characters", 1_000)
    messages = []
    monkeypatch.setattr(extension.controller, "present_message_internal", messages.append)

    extension._start_translation("x" * 1_001)

    assert extension._coordinator.requests == []
    assert "1,001 characters" in messages[0]


def test_google_input_is_not_limited_by_paid_provider_guard(extension):
    extension.settings.set("engine", "google")
    extension.settings.set("max-input-characters", 1_000)
    extension._start_translation("x" * 1_001)
    assert extension._coordinator.requests[-1].engine == "google"


def test_deepl_plaintext_key_is_stripped_and_removed_from_settings(extension):
    extension.settings.set("engine", "deepl")
    extension.settings.set("deepl-api-key", "  secret  ")
    extension.settings.set("deepl-plan", "pro")

    extension._start_translation("hello")

    request = extension._coordinator.requests[-1]
    assert request.deepl_api_key == "secret"
    assert request.deepl_plan == "pro"
    assert extension.settings.get("deepl-api-key", default="missing") == "missing"
    assert "secret" not in repr(request)


def test_deepl_execution_reads_stored_key(extension, monkeypatch):
    extension._secret_store = _FakeSecretStore("stored-secret")
    captured = {}

    class _Backend:
        def __init__(self, api_key, plan):
            captured.update(api_key=api_key, plan=plan)

        def translate(self, request, cancel_event):
            return TranslationResult("hallo", "en")

    monkeypatch.setattr("instant_translate.extension.DeepLBackend", _Backend)
    result = extension._execute_translation(
        _request(engine="deepl", target_language="DE", deepl_plan="free"),
        threading.Event(),
    )

    assert result.translation == "hallo"
    assert captured == {"api_key": "stored-secret", "plan": "free"}


def test_deepl_execution_without_any_key_returns_specific_error(extension):
    result = extension._execute_translation(
        _request(engine="deepl", target_language="DE"),
        threading.Event(),
    )
    assert result.error_kind == ErrorKind.AUTHENTICATION
    assert result.error_message == "DeepL API key is not set."


def test_deepl_new_key_is_migrated_to_secret_store(extension, monkeypatch):
    extension._secret_store = _FakeSecretStore()

    class _Backend:
        def __init__(self, _api_key, _plan):
            pass

        def translate(self, request, cancel_event):
            return TranslationResult("hallo", "en")

    monkeypatch.setattr("instant_translate.extension.DeepLBackend", _Backend)
    result = extension._execute_translation(
        _request(engine="deepl", target_language="DE", deepl_api_key="new-secret"),
        threading.Event(),
    )
    assert result.ok
    assert extension._secret_store.stored == ["new-secret"]


def test_finish_translation_uses_specific_error_message(extension, monkeypatch):
    messages = []
    monkeypatch.setattr(extension.controller, "present_message_internal", messages.append)
    monkeypatch.setattr(extension.controller, "play_tone_internal", lambda *_a: None)

    result = TranslationResult.failure(
        ErrorKind.AUTHENTICATION,
        "The DeepL API key is invalid.",
    )
    extension._finish_translation(
        1,
        _request(engine="deepl", target_language="DE"),
        result,
        True,
    )
    assert messages == ["The DeepL API key is invalid."]


def test_finish_translation_falls_back_to_generic_message(extension, monkeypatch):
    messages = []
    monkeypatch.setattr(extension.controller, "present_message_internal", messages.append)
    monkeypatch.setattr(extension.controller, "play_tone_internal", lambda *_a: None)
    result = TranslationResult(error_kind=ErrorKind.UNKNOWN)

    extension._finish_translation(1, _request(), result, True)

    assert messages == ["Translation failed."]


def test_cache_hit_supersedes_network_work(extension, monkeypatch):
    extension.settings.set("engine", "google")
    extension.settings.set("google-to-language", "en")
    extension.settings.set("cache-translations", True)
    extension._translation_cache[("google", "auto", "en", "hello")] = "bonjour"
    messages = []
    monkeypatch.setattr(extension.controller, "present_message_internal", messages.append)

    extension._start_translation("hello")

    assert extension._coordinator.requests == []
    assert extension._coordinator.superseded == 1
    assert messages == ["bonjour"]


def test_successful_latest_result_populates_cache(extension, monkeypatch):
    messages = []
    monkeypatch.setattr(extension.controller, "present_message_internal", messages.append)
    cache_key = ("google", "auto", "en", "hello")
    request = _request(cache_key=cache_key)

    extension._finish_translation(1, request, TranslationResult("bonjour", "fr"), True)

    assert extension._translation_cache[cache_key] == "bonjour"
    assert messages == ["bonjour"]


def test_stale_result_is_not_presented_or_cached(extension, monkeypatch):
    messages = []
    monkeypatch.setattr(extension.controller, "present_message_internal", messages.append)
    cache_key = ("google", "auto", "en", "old")

    extension._finish_translation(
        1,
        _request(text="old", cache_key=cache_key),
        TranslationResult("old result", "fr"),
        False,
    )

    assert messages == []
    assert cache_key not in extension._translation_cache


def test_result_that_became_stale_while_waiting_for_idle_is_ignored(extension, monkeypatch):
    messages = []
    monkeypatch.setattr(extension.controller, "present_message_internal", messages.append)
    request = _request()
    request_id = extension._coordinator.submit(request)
    extension._coordinator.supersede()

    extension._finish_translation(
        request_id,
        request,
        TranslationResult("stale", "en"),
        True,
    )

    assert messages == []


def test_identification_uses_request_engine_label(extension, monkeypatch):
    extension.settings.set("engine", "google")
    messages = []
    monkeypatch.setattr(extension.controller, "present_message_internal", messages.append)

    extension._finish_translation(
        1,
        _request(engine="yandex", identify_only=True),
        TranslationResult("unused", "ba"),
        True,
    )

    assert messages == ["Detected language: Bashkir"]


def test_clipboard_translation_is_requested_asynchronously(extension, monkeypatch):
    callbacks = []
    monkeypatch.setattr(extension, "_request_clipboard_text", callbacks.append)

    assert extension.translate_clipboard() is True
    assert extension._coordinator.requests == []

    callbacks[0]("clipboard text")
    assert extension._coordinator.requests[-1].text == "clipboard text"


def test_deepl_swap_normalizes_regional_target_to_base_source(extension, monkeypatch):
    extension.settings.set("engine", "deepl")
    extension.settings.set("deepl-from-language", "DE")
    extension.settings.set("deepl-to-language", "EN-GB")
    monkeypatch.setattr(extension.controller, "present_message_internal", lambda *_a: None)
    monkeypatch.setattr(extension, "_get_selected_text", lambda: None)

    extension.swap_languages()

    assert extension.settings.get("deepl-from-language") == "EN"
    assert extension.settings.get("deepl-to-language") == "DE"

import io
import json
import urllib.error as urllib_error
import urllib.parse as urllib_parse

from instant_translate.backends.deepl import DeepLBackend
from instant_translate.models import TranslationRequest
from instant_translate.text_chunking import smart_split


class _FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_exc_info):
        self.close()


class _FakeOpener:
    def __init__(self, responses=None, http_error=None):
        self.responses = list(responses or [])
        self.http_error = http_error
        self.requests = []

    def open(self, request, timeout=None):
        self.requests.append(request)
        if self.http_error is not None:
            raise self.http_error
        payload = self.responses.pop(0)
        return _FakeResponse(json.dumps(payload).encode("utf-8"))


def _request(text="hi", source="auto", target="DE"):
    return TranslationRequest("deepl", source, target, text)


def test_free_plan_uses_free_endpoint():
    backend = DeepLBackend("k", plan="free")
    assert backend.endpoint == DeepLBackend.FREE_URL


def test_pro_plan_uses_pro_endpoint():
    backend = DeepLBackend("k", plan="pro")
    assert backend.endpoint == DeepLBackend.PRO_URL


def test_successful_translation():
    backend = DeepLBackend(
        "k",
        opener=_FakeOpener(
            [{"translations": [{"detected_source_language": "EN", "text": "hallo"}]}]
        ),
    )

    result = backend.translate(_request("hello"))

    assert result.translation == "hallo"
    assert result.detected_language == "en"
    assert result.ok
    assert result.error_message is None


def test_auth_header_uses_deepl_auth_key_prefix():
    opener = _FakeOpener(
        [{"translations": [{"detected_source_language": "EN", "text": "hi"}]}]
    )
    backend = DeepLBackend("secret-key", opener=opener)

    backend.translate(_request())

    assert opener.requests[0].get_header("Authorization") == "DeepL-Auth-Key secret-key"


def test_source_lang_omitted_when_auto():
    opener = _FakeOpener(
        [{"translations": [{"detected_source_language": "EN", "text": "hi"}]}]
    )
    backend = DeepLBackend("k", opener=opener)

    backend.translate(_request())

    body = opener.requests[0].data.decode("utf-8")
    assert "source_lang" not in body


def test_source_lang_included_when_set():
    opener = _FakeOpener(
        [{"translations": [{"detected_source_language": "EN", "text": "hi"}]}]
    )
    backend = DeepLBackend("k", opener=opener)

    backend.translate(_request(source="EN"))

    body = opener.requests[0].data.decode("utf-8")
    assert "source_lang=EN" in body


def test_http_error_maps_to_friendly_message():
    opener = _FakeOpener(
        http_error=urllib_error.HTTPError("url", 403, "Forbidden", {}, None)
    )
    backend = DeepLBackend("bad-key", opener=opener)

    result = backend.translate(_request())

    assert not result.ok
    assert result.error_message == DeepLBackend.ERRORS[403]


def test_unmapped_http_error_includes_safe_http_status():
    opener = _FakeOpener(
        http_error=urllib_error.HTTPError("url", 500, "Server Error", {}, None)
    )
    backend = DeepLBackend("k", opener=opener)
    backend.client.max_attempts = 1

    result = backend.translate(_request())

    assert not result.ok
    assert result.error_message == "DeepL request failed (HTTP 500)."


def test_long_text_is_split_into_multiple_chunks_and_concatenated():
    long_text = ("word " * 2000).strip()
    expected_chunks = len(smart_split(long_text, 5000, 5500))
    assert expected_chunks > 1
    opener = _FakeOpener(
        [
            {
                "translations": [
                    {"detected_source_language": "EN", "text": f"part{i} "}
                ]
            }
            for i in range(expected_chunks)
        ]
    )
    backend = DeepLBackend("k", opener=opener)

    result = backend.translate(_request(long_text))

    assert result.translation == "".join(f"part{i} " for i in range(expected_chunks))
    assert result.ok


def test_non_latin_script_chunk_stays_under_deepls_request_size_limit():
    worst_case_chunk = "国" * 5500
    params = {"text": worst_case_chunk, "target_lang": "DE", "source_lang": "EN"}
    encoded_len = len(urllib_parse.urlencode(params).encode("utf-8"))
    assert encoded_len < 131072


def test_empty_api_key_still_attempts_request_error_handling_is_callers_job():
    opener = _FakeOpener(
        [{"translations": [{"detected_source_language": "EN", "text": "hi"}]}]
    )
    backend = DeepLBackend("", opener=opener)

    backend.translate(_request())

    assert opener.requests[0].get_header("Authorization") == "DeepL-Auth-Key "

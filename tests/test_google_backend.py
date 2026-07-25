import io
import json
import ssl
from urllib.parse import parse_qs, urlparse

from instant_translate.backends.google import GoogleBackend
from instant_translate.google_chunking import split_chunks
from instant_translate.models import TranslationRequest


class _FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_exc_info):
        self.close()


class _FakeOpener:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []
        self.addheaders = []

    def open(self, request, timeout=None):
        self.requests.append(request)
        payload = self.responses.pop(0)
        return _FakeResponse(json.dumps(payload).encode("utf-8"))


def _payload(text, source="en"):
    return {"src": source, "sentences": [{"trans": text}]}


def _request(text="hello world", source="auto", target="tr", mirror=False):
    return TranslationRequest(
        "google",
        source,
        target,
        text,
        use_mirror=mirror,
    )


def test_import_does_not_disable_tls_verification():
    assert ssl._create_default_https_context is not ssl._create_unverified_context


def test_successful_google_translation_and_request_encoding():
    opener = _FakeOpener([_payload("merhaba dünya")])
    backend = GoogleBackend(split_chunks, opener=opener)

    result = backend.translate(_request())

    assert result.translation == "merhaba dünya"
    assert result.detected_language == "en"
    assert result.ok
    query = parse_qs(urlparse(opener.requests[0]).query)
    assert query["sl"] == ["auto"]
    assert query["tl"] == ["tr"]
    assert query["q"] == ["hello world"]


def test_google_language_fixup_is_applied():
    backend = GoogleBackend(
        split_chunks,
        opener=_FakeOpener([_payload("hello", source="iw")]),
    )

    result = backend.translate(_request("שלום", target="en"))

    assert result.detected_language == "he"


def test_google_backend_processes_every_chunk_from_existing_splitter_contract():
    chunks = ["first", "second", "third"]
    opener = _FakeOpener([_payload("1"), _payload("2"), _payload("3")])
    backend = GoogleBackend(lambda _text, _size: iter(chunks), opener=opener)

    result = backend.translate(_request("ignored", target="en"))

    assert result.translation == "123"
    assert len(opener.requests) == len(chunks)


def test_google_splitter_retains_legacy_long_punctuation_behavior():
    # The user explicitly requested that Google chunking remain unchanged.
    assert [len(chunk) for chunk in split_chunks("a" * 4000 + ".", 3000)] == [1, 4000]


def test_malformed_google_response_returns_specific_safe_error():
    backend = GoogleBackend(split_chunks, opener=_FakeOpener([{"unexpected": "shape"}]))

    result = backend.translate(_request("private selected text", target="en"))

    assert not result.ok
    assert result.error_message == "Google Translate returned an invalid response."
    assert "private selected text" not in (result.diagnostic or "")
